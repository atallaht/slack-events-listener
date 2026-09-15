FROM python:3.12-alpine

RUN apk add --no-cache su-exec tini

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY slack_events_server.py .

ENV PYTHONUNBUFFERED=1
ENV SLACK_BIND=0.0.0.0:3010
ENV SLACK_INBOX_PATH=/data/inbox.jsonl

EXPOSE 3010

ENTRYPOINT ["/sbin/tini", "--"]
CMD ["python", "slack_events_server.py"]
