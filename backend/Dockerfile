# ---- Stage 1: build dependencies ----
FROM python:3.12-slim AS builder
WORKDIR /build
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Stage 2: runtime ----
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY app.py .
RUN useradd --system --no-create-home --uid 10001 appuser
USER 10001
EXPOSE 5000
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]