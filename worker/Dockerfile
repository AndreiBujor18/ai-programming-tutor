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
    && useradd --uid 65533 --gid 65532 --no-create-home --shell /usr/sbin/nologin aptutor-untrusted \
    && install --directory --owner=65532 --group=65532 --mode=0700 /work \
    && install --directory --owner=0 --group=0 --mode=0700 /opt/aptutor-private

WORKDIR /opt/aptutor
COPY pyproject.toml README.md ./
COPY src ./src
RUN python -m pip install --no-cache-dir --no-deps . \
    && package_root="$(python -c 'from pathlib import Path; import ai_programming_tutor; print(Path(ai_programming_tutor.__file__).resolve().parent)')" \
    && chown --recursive 0:0 "$package_root" \
    && chmod --recursive go-rwx "$package_root" \
    && rm --recursive --force /opt/aptutor/src
COPY --chown=0:0 --chmod=0600 worker/protected_canary.h \
    /opt/aptutor-private/protected_canary.h

# A bare image run cannot read the controller package. The reviewed host command
# explicitly selects namespace UID 0 while retaining only CAP_KILL and
# CAP_SETUID, then the controller drops compiler and program subprocesses to
# UID 65533 and clears escaped descendants between tests.
USER 65532:65532
WORKDIR /work
ENTRYPOINT ["python", "-m", "ai_programming_tutor.worker"]
