FROM ghcr.io/astral-sh/uv:python3.13-bookworm AS build

RUN mkdir -p /build
WORKDIR /build
COPY . /build/

RUN uv export --no-dev -o requirements.txt

FROM python:3.13-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    iptables \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /app
WORKDIR /app

COPY --from=build /build/requirements.txt /build/main.py /app/
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]
