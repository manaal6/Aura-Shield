FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Serve the deployed console (FastAPI + React bundle), matching render.yaml.
# The Streamlit lab (dashboard/) remains local-only via `streamlit run dashboard/streamlit_app.py`.
EXPOSE 8000

CMD ["uvicorn", "webapp.server:app", "--host", "0.0.0.0", "--port", "8000"]
