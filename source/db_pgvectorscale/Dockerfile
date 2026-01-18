# TimeScaleDB with pgvector and vector scaling extension
# FROM timescale/timescaledb:latest-pg18
FROM timescale/timescaledb:2.23.1-pg18

# Copy initialization scripts for adding extension and database
COPY 111-create-user-db.sh /docker-entrypoint-initdb.d/111-create-user-db.sh
RUN chmod +x /docker-entrypoint-initdb.d/111-create-user-db.sh