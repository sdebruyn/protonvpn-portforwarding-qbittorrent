FROM ghcr.io/astral-sh/uv:python3.13-alpine AS build

RUN mkdir -p /build
WORKDIR /build
COPY . /build/

RUN uv export --no-dev -o requirements.txt

FROM python:3.13-alpine

RUN apk add --no-cache iptables-legacy

RUN mkdir -p /app
WORKDIR /app

COPY --from=build /build/requirements.txt /build/main.py /app/
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]
