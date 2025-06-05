# FROM python:3.11-slim

# WORKDIR /app

# COPY deface_checker.py .

# COPY model/ ./model/

# COPY requirements.txt .
# # COPY .env .env # no need! Just use .env at docker compose

# # Install dependencies
# RUN pip install --no-cache-dir -r requirements.txt
# RUN apt-get update \
#     && apt-get install -y iputils-ping \
#     && apt-get install -y telnet \
# #     && apt-get install -y curl \
# #     && apt-get install -y wget \
# #     && apt-get install -y git \
#     && apt-get clean

# # CMD ["tail", "-f", "/dev/null"]
# CMD ["python", "-u", "deface_checker.py"]


# Base image — chỉ cần build 1 lần
FROM python:3.11-slim AS base
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update \
    && apt-get install -y --no-install-recommends iputils-ping \
    && apt-get install -y --no-install-recommends telnet \
    && apt-get install -y --no-install-recommends curl \
    # && apt-get install -y --no-install-recommends wget \
    # && apt-get install -y --no-install-recommends git \
    && apt-get clean

# Final image — rebuild nhanh khi code thay đổi
FROM base AS final
WORKDIR /app
COPY . .
CMD ["python", "-u", "deface_checker.py"]