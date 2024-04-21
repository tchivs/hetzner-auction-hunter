FROM python:3.11-slim-bookworm

LABEL desc="hetzner-auction-hunter"
LABEL website="https://github.com/danielskowronski/hetzner-auction-hunter"

COPY requirements.txt /requirements.txt
RUN python3 -m pip install --no-cache-dir -r /requirements.txt

COPY hah.py /hah.py

ENTRYPOINT [ "./hah.py" ]
