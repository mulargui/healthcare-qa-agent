FROM python:3.12-slim

WORKDIR /app

COPY infra/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agent/src/ src/
COPY agent/tests/ tests/

ENTRYPOINT ["python", "src/main.py"]
