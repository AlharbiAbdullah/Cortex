FROM apache/superset:latest

USER root

# Install PostgreSQL driver into the venv
RUN uv pip install --python /app/.venv/bin/python psycopg2-binary

USER superset
