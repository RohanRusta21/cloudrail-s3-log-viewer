FROM python:3.9-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN python -m venv /venv && \
    /venv/bin/pip install --no-cache-dir -r requirements.txt
COPY . .
FROM python:3.9-slim
WORKDIR /app
COPY --from=builder /venv /venv
COPY . .
ENV PATH="/venv/bin:$PATH"
EXPOSE 5000
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
CMD ["flask", "run"]
