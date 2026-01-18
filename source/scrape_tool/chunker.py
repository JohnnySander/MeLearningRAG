import json
import logging
import os
from pathlib import Path
import re

import dotenv
from openai import OpenAI
import psycopg2
from pydantic import BaseModel, Field

from db_sqlite import connect_db, check_table_exists
from logger import setup_logger

SAVEFOLDER = Path('./res_folder')

dotenv.load_dotenv()

if __name__ == "__main__":
    logger = setup_logger(__name__, logging.DEBUG)
else:
    logger = logging.getLogger(__name__)

# Initialize OpenAI client for embeddings
openai_client_emb = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY', ""),
    base_url=os.getenv('EMBEDDING_BASE_URL', "")
)
# Initialize OpenAI client for summarization
openai_client_sum = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY', ""),
    base_url=os.getenv('SUMMARIZATION_BASE_URL', "")
)


class SitePageResult(BaseModel):
    url: str = Field(..., description="The URL of the web page.")
    content: str = Field(..., description="The textual content of the web page.")
    summary: str = Field(..., description="A brief summary of the web page content.")
    metadata: dict = Field(..., description="Metadata associated with the web page.")


class ChunkResult(BaseModel):
    chunk_number: int = Field(..., description="The chunk number.")
    url: str = Field(..., description="The URL of the web page.")
    content: str = Field(..., description="A chunk of the web page content.")


class ProcessedChunk(BaseModel):
    url: str = Field(..., description="The URL of the web page.")
    chunk_number: int = Field(..., description="The chunk number.")
    title: str = Field(..., description="Title of the chunk.")
    summery: str = Field(..., description="Summary of the chunk.")
    content: str = Field(..., description="Content of the chunk.")
    metadata: dict = Field(..., description="Metadata associated with the chunk.")
    chunk_vector: list[float] = Field(..., description="Vector representation of the chunk.")


def content_summary(content: str) -> dict:
    """
        Extract title and a summary for the given content by calling the summarization LLM.
    """
    system_prompt = """You are an AI that extracts titles and summaries from documentation chunks.
    Return a JSON object with 'title' and 'summary' keys.
    For the title: If this seems like the start of a document, extract its title.
    If it's a middle chunk, derive a descriptive title.
    For the summary: Create a concise summary of the main points in this chunk.
    Keep both title and summary concise but informative."""

    try:
        response = openai_client_sum.chat.completions.create(
            # model=os.getenv('SUMMARIZATION_LLM', ""),
            model='ai/smollm3:latest',
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content}
            ],
            response_format={"type": "json_object"},
        )
        assert response.choices[0].message.content is not None
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logger.debug('Summarization request failed: %s', e)
        raise e


def vectorize_text(text: str) -> list[float]:
    """
        Convert text to a vector representation.
    """
    logger.info('Generating embedding for text of length %d', len(text))
    try:
        response = openai_client_emb.embeddings.create(
            model=os.getenv('EMBEDDING_LLM', ""),
            input=text
        )
        logger.info('Generated embedding of length %d', len(response.data[0].embedding))
        # assert len(response.data[0].embedding) == 769  # Example: Check for 1536-dimensional embedding
        return response.data[0].embedding
    except Exception as e:
        logger.debug('Embedding request failed: %s', e)
        raise e


def md_chunk_content(markdown: str, max_len: int = 800) -> list[str]:
    """
        Hierarchically splits markdown by #, ##, ### headers,
        then by characters, to ensure all chunks < max_len.
    """
    def split_by_header(md, header_pattern):
        indices = [m.start() for m in re.finditer(header_pattern,
                                                  md,
                                                  re.MULTILINE)]
        indices.append(len(md))
        return [md[indices[i]:indices[i+1]].strip()
                for i in range(len(indices)-1)
                if md[indices[i]:indices[i+1]].strip()]

    chunks = []

    # Split by headers as needed to get under max_len
    for h1 in split_by_header(markdown, r'^# .+$'):
        if len(h1) <= max_len:
            chunks.append(h1)
        for h2 in split_by_header(h1, r'^## .+$'):
            if len(h2) <= max_len:
                chunks.append(h2)
            for h3 in split_by_header(h2, r'^### .+$'):
                if len(h3) <= max_len:
                    chunks.append(h3)
                    # Further split by string length if still too long
                    for i in range(0, len(h3), max_len):
                        chunks.append(h3[i:i+max_len].strip())

    final_chunks = []
    for c in chunks:
        if len(c) > max_len:
            final_chunks.extend([c[i:i+max_len].strip()
                                 for i in range(0, len(c), max_len)])
        else:
            final_chunks.append(c)

    return [c for c in final_chunks if c]


def vec_process_content(url: str, content: str) -> list[ProcessedChunk]:
    """
        Process and store content into vector database.
    """
    # page_summary = content_summary(content)
    page_result: SitePageResult = SitePageResult(
        url=url,
        content=content,
        summary="",
        metadata={},
    )

    chunked_content: list[str] = md_chunk_content(page_result.content)
    chunk_results: list[ProcessedChunk] = []
    for i, chunk in enumerate(chunked_content):
        chunk_summary = content_summary(chunk)
        chunk_embedding = vectorize_text(chunk)

        processed_chunk = ProcessedChunk(
            url=url,
            chunk_number=i,
            title=chunk_summary['title'],
            summery=chunk_summary['summary'],
            content=chunk,
            metadata=page_result.metadata,
            chunk_vector=chunk_embedding
        )
        chunk_results.append(processed_chunk)

    return chunk_results


def vec_store(processed_chunks: list[ProcessedChunk]) -> None:
    """
    Save processed chunks into PostgreSQL database with pgvector.

    :param processed_chunks: Description
    :type processed_chunks: list[ProcessedChunk]
    """
    # Connect to PostgreSQL database
    conn = psycopg2.connect(
        dbname=os.getenv('POSTGRES_NAME', ''),
        user=os.getenv('POSTGRES_USER', ''),
        password=os.getenv('POSTGRES_PASSWORD', ''),
        host=os.getenv('POSTGRES_HOST', ''),
        port=os.getenv('POSTGRES_PORT', '5432')
    )
    cur = conn.cursor()

    # Insert processed chunks
    for chunk in processed_chunks:
        cur.execute("""
            INSERT INTO web_embedding (url, chunk_index, title, summary, content, metadata, embedding)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """, (
            chunk.url,
            chunk.chunk_number,
            chunk.title,
            chunk.summery,
            chunk.content,
            json.dumps(chunk.metadata),
            chunk.chunk_vector
        ))
    conn.commit()
    conn.close()
    return


def main(site: str) -> None:
    """
    Main function for processing scraped web content into vector database.

    :param site: Site identifier, identifying
    :type site: str
    """

    logger.info(f'Vectorizing content for site: {site}')
    db_path = SAVEFOLDER / site / 'pages.db'
    conn = connect_db(db_path)
    logger.info(f'Connected to SQLitedatabase at {db_path}.')

    if not check_table_exists(conn, 'pages'):
        logger.error(f"No 'pages' table found in database at {db_path}.")
        conn.close()
        return

    # Fetch all content for site from pages database
    cur = conn.cursor()
    cur.execute('SELECT url, content FROM pages WHERE site = ?', (site,))
    rows = cur.fetchall()
    conn.close()
    for url, content in rows:
        processed_chunks = vec_process_content(url, content)
        vec_store(processed_chunks)


if __name__ == "__main__":
    # setup_logger(__name__, logging.DEBUG)
    sites = ['PySide6', 'StreamLit', 'PydanticAI']
    for site in sites:
        logger.info(f'Starting chunking for site: {site}')
        main(site)
