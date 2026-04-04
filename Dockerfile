
FROM python:3.10-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir pydantic openai
ENV API_BASE_URL="https://api.openai.com/v1"
ENV MODEL_NAME="gpt-4o-mini"
ENV HF_TOKEN=""

CMD ["python", "inference.py"]