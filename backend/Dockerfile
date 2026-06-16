FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install -e .
COPY src ./src
CMD ["uvicorn", "agent_bazaar.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
