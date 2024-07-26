FROM python:3.11-slim-bookworm

LABEL desc="hetzner-auction-hunter"
LABEL website="https://github.com/danielskowronski/hetzner-auction-hunter"

# Define Application Path
ARG APP_PATH="/opt/app"

# Define venv Path
ARG VENV_PATH="/opt/venv"

# Use Cache (Keep downloaded Files)
# They are stored in the Cache directory, NOT in the final Container Image
RUN rm -f /etc/apt/apt.conf.d/docker-clean; echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache

# Install CURL & wget
RUN apt-get update && \
    apt-get install --yes curl wget

# Copy Sources
COPY app/ ${APP_PATH}

# Create venv
RUN python3 -m venv "${VENV_PATH}"

# Set PATH Variable to include venv
ENV PATH="${VENV_PATH}/bin:$PATH"

# Activate venv and install dependencies
RUN . "${VENV_PATH}/bin/activate" && \
    pip install -r "${APP_PATH}/requirements.txt"

# Install Shdotenv
RUN curl -s "https://github.com/ko1nksm/shdotenv/releases/latest/download/shdotenv" -o "/usr/local/bin/shdotenv"

# Ensure correct Permissions
RUN chmod +x /usr/local/bin/shdotenv

# Set PATH Variable to Include shdotenc
ENV PATH="$PATH:/usr/local/bin"

# Change Directory
WORKDIR "${APP_PATH}"

# Run Command
ENTRYPOINT ["python", "hah.py"]
