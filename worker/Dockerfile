FROM python:3.12-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOME=/nonexistent \
    TMPDIR=/work \
    TMP=/work \
    TEMP=/work

RUN apt-get update \
    && apt-get install --yes --no-install-recommends gcc libc6-dev \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 65532 aptutor \
    && useradd --uid 65532 --gid 65532 --no-create-home --shell /usr/sbin/nologin aptutor \
    && install --directory --owner=65532 --group=65532 --mode=0700 /work

WORKDIR /opt/aptutor
COPY pyproject.toml README.md ./
COPY src ./src
RUN python -m pip install --no-cache-dir --no-deps .

USER 65532:65532
WORKDIR /work
ENTRYPOINT ["python", "-m", "ai_programming_tutor.worker"]
