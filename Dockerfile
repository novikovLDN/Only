FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Health check
EXPOSE 8080

# Migrations before app start (uses asyncpg, same as app)
CMD ["sh", "-c", "alembic upgrade head && python run.py"]
