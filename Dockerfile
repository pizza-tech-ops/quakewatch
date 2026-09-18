FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY quakewatch/ quakewatch/
COPY tests/ tests/

ENV PYTHONPATH=/app
ENV QUAKEWATCH_DB=/data/quakes.db

EXPOSE 8000

CMD ["uvicorn", "quakewatch.api:app", "--host", "0.0.0.0", "--port", "8000"]
