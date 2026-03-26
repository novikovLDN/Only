# Stage 1: Install dependencies
FROM python:3.12-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --target=/deps -r requirements.txt

# Stage 2: Production image
FROM python:3.12-slim

WORKDIR /app

# Copy only dependencies and app code
COPY --from=builder /deps /usr/local/lib/python3.12/site-packages/
COPY --from=builder /deps/bin/* /usr/local/bin/
COPY app/ ./app/
COPY VERSION ./

# Non-root user for security
RUN useradd --system --no-create-home botuser
USER botuser

CMD ["sh", "-c", "python -m app.main & uvicorn app.health:app --host 0.0.0.0 --port ${PORT:-8080}"]
