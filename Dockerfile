FROM python:3.11-slim-bookworm

LABEL desc="hetzner-auction-hunter"
LABEL website="https://github.com/danielskowronski/hetzner-auction-hunter"

# Copy Sources
COPY app/ /opt/app

# Change Directory
WORKDIR "/opt/app"

# Install Required Python Modules
RUN python3 -m pip install --no-cache-dir -r /opt/app/requirements.txt

# Run Command
ENTRYPOINT [ "./hah.py" ]
