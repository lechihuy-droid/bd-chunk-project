FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV OPUS_HARNESS_SANDBOX=docker

RUN useradd --create-home --uid 10001 harness
COPY harness/sandbox/entrypoint.sh /usr/local/bin/opus-harness-entrypoint
RUN chmod 755 /usr/local/bin/opus-harness-entrypoint

USER harness
WORKDIR /work/repo
ENTRYPOINT ["opus-harness-entrypoint"]
CMD ["workspace-smoke"]
