FROM python:3.11-slim

WORKDIR /app

COPY deface_checker.py .

COPY model/ ./model/

COPY requirements.txt .
# COPY .env .env # use .env when docker compose up

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update \
    && apt-get install -y iputils-ping \
    && apt-get install -y telnet \
#     && apt-get install -y curl \
#     && apt-get install -y wget \
#     && apt-get install -y git \
    && apt-get clean

# CMD ["tail", "-f", "/dev/null"]
CMD ["python", "-u", "deface_checker.py"]
