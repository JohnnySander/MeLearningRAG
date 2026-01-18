# Header

## From Cole Medin repository

Rep <https://github.com/coleam00/local-ai-packaged.git>

## Dave Ebbelaar

<https://github.com/daveebbelaar>

## Docker reference documentation

<https://docs.docker.com/reference>

## PostgreSQL

<https://www.postgresql.org/docs/current/index.html>

## PGVector

<https://github.com/pgvector/pgvector>
pip install pgvector

## PGVectorScale

<https://github.com/timescale/pgvectorscale>
<https://github.com/daveebbelaar/pgvectorscale-rag-solution>

## PGai

<https://github.com/timescale/pgai>
<https://hub.docker.com/u/timescale>
pip install pgai
-- from the cli
pgai install -d <database-url>

-- or from the python package, often done as part of your application setup
import pgai
pgai.install(DB_URL)

-- Quickstart main.py
<https://github.com/timescale/pgai/blob/main/examples/quickstart/main.py>

## Crawl4AI

<https://docs.crawl4ai.com/>
<https://github.com/unclecode/crawl4ai>
<https://github.com/coleam00/ottomator-agents/tree/main/crawl4AI-agent-v2>

## Streamlit UI

A simple Streamlit-based interface to run the scraper interactively has been added at `source/scrape_tool/streamlit_ui.py`.

- Purpose: provide form fields for *Site name* and *URL* (both required) and an optional *Search pattern*, then call `scraper.main(site, url, pattern)`.
- Run locally:

```bash
pip install streamlit
streamlit run source/scrape_tool/streamlit_ui.py
```

Notes:

- If the search pattern is left empty the scraper will use the default `*` pattern.
- The UI dynamically loads `source/scrape_tool/scraper.py` and executes `main(...)`, so run the Streamlit app from the repository root to ensure relative paths behave as expected.
