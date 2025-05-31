FROM python:3.11-slim

WORKDIR /app

COPY deface_checker.py .

COPY model/ ./model/

COPY requirements.txt .
COPY .env.example .env

# 4. Cài đặt thư viện
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y iputils-ping \
    && apt-get install -y curl \
    && apt-get install -y wget \
    && apt-get install -y git \
    && apt-get clean

CMD ["tail", "-f", "/dev/null"]
# CMD ["python", "deface_checker.py"]
