FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_PORT=8501

WORKDIR /app

COPY pyproject.toml requirements.txt ./
COPY euler ./euler
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY .streamlit/config.toml ./.streamlit/config.toml
COPY templates ./templates
COPY demo ./demo
COPY validation ./validation
COPY docs ./docs

EXPOSE 8501

CMD ["streamlit", "run", "app/main.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
