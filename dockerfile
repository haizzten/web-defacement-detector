FROM python:3.11-slim

WORKDIR /app

COPY deface_checker.py .

COPY model/ ./model/

RUN pip install joblib requests beautifulsoup4

CMD ["python", "deface_checker.py"]
