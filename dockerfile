# Example Dockerfile structure
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY app/ ./app/
# Environment variables for CORS configuration
#ENV CORS_ORIGINS="https://your-frontend-domain.com,https://another-domain.com"

#CMD ["uvicorn", "app.chat_server:app", "--host", "0.0.0.0", "--port", "8000"]

CMD ["sh", "-c", "uvicorn app.chat_server:app --host 0.0.0.0 --port ${PORT:-8000}"]
