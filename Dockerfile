FROM python:3.11-slim-bookworm

LABEL desc="hetzner-auction-hunter"
LABEL website="https://github.com/danielskowronski/hetzner-auction-hunter"

# Update APT Sources
RUN apt-get update

# Install CURL & wget
RUN apt-get install --yes curl wget

# Clear APT cache
RUN apt-get clean

# Copy Sources
COPY app/ /opt/app

# Create venv
RUN python3 -m venv "/opt/venv"

# Set PATH Variable to include venv
ENV PATH="$PATH:/opt/venv"

# Try more POSIX compliant Solution
# This works correclty
RUN sh -c ". /opt/venv/bin/activate"

# Install Shdotenv
#RUN wget "https://github.com/ko1nksm/shdotenv/releases/latest/download/shdotenv" -O "/usr/local/bin/shdotenv"
RUN curl -s "https://github.com/ko1nksm/shdotenv/releases/latest/download/shdotenv" -o "/usr/local/bin/shdotenv"

# Ensure correct Permissions
RUN chmod +x /usr/local/bin/shdotenv

# Set PATH Variable to Include shdotenc
ENV PATH="$PATH:/usr/local/bin"

# Install required Packages
RUN pip install --no-cache-dir -r /opt/app/requirements.txt

# Change Directory
WORKDIR "/opt/app"

# Run Command
ENTRYPOINT [ "./hah.py" ]
