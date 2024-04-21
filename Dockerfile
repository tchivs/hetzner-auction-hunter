FROM python:3.11-slim-bookworm

LABEL desc="hetzner-auction-hunter"
LABEL website="https://github.com/danielskowronski/hetzner-auction-hunter"

# Copy Sources
COPY app/ /opt/app

# Create venv
RUN python3 -m venv "/opt/venv"

# Set PATH Variable to include venv
ENV PATH="$PATH:/opt/venv"

# Activate venv
# This however requires BASH
#RUN source "/opt/venv/bin/activate"

# Try more POSIX compliant Solution
RUN sh -c ". /opt/venv/bin/activate"

# Set PATH Variable to Include venv
#ENV PATH="$PATH:/opt/venv"

# Install required Packages
RUN pip install --no-cache-dir -r /opt/app/requirements.txt

# Change Directory
WORKDIR "/opt/app"

# Run Command
ENTRYPOINT [ "./hah.py" ]
