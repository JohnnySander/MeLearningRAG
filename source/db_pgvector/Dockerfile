FROM pgvector/pgvector:pg18-trixie

# Copy initialization scripts for adding extension and database
COPY 111-create-user-db.sh /docker-entrypoint-initdb.d/111-create-user-db.sh
RUN chmod +x /docker-entrypoint-initdb.d/111-create-user-db.sh
