# Header

## From Cole Medin repository

Rep <https://github.com/coleam00/local-ai-packaged.git>

## Docker refernce documentation

<https://docs.docker.com/reference>

## PostgreSQL

<https://www.postgresql.org/docs/current/index.html>

## PGVector

<https://github.com/pgvector/pgvector>
pip install pgvector

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