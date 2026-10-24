# SPDX-License-Identifier: AGPL-3.0-or-later
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    CTRANSLATE2_INTER_THREADS=2

WORKDIR /app
COPY requirements-translation.txt /app/requirements-translation.txt
RUN python -m pip install --no-cache-dir -r requirements-translation.txt
COPY saylacian /app/saylacian
COPY tools/prepare_models.py /app/tools/prepare_models.py
COPY cloud/oci/service.py /app/cloud/oci/service.py
RUN python /app/tools/prepare_models.py --download

RUN useradd --system --uid 10001 saylacian && chown -R saylacian:saylacian /app
USER 10001:10001
EXPOSE 8080
CMD ["python", "-m", "cloud.oci.service"]
