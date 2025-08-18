FROM ghcr.io/astral-sh/uv:python3.13-alpine AS build

RUN mkdir -p /build
WORKDIR /build
COPY . /build/

RUN uv export --no-dev -o requirements.txt

FROM python:3.13.7-alpine

RUN mkdir -p /app
WORKDIR /app

COPY --from=build /build/requirements.txt /build/main.py /build/healthcheck.sh /app/
RUN chmod +x /app/healthcheck.sh
RUN pip install --no-cache-dir -r requirements.txt


HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD ["/app/healthcheck.sh"]

CMD ["python", "main.py"]
