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
RUN --mount=type=cache,mode=0777,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,mode=0777,target=/var/lib/apt,sharing=locked \
    apt-get update && \
    apt-get install --yes curl wget

# Copy Sources
COPY app/ ${APP_PATH}

# Create venv
RUN python3 -m venv "${VENV_PATH}"

# Set PATH Variable to include venv
ENV PATH="$PATH:${VENV_PATH}"

# Try more POSIX compliant Solution
# This works correclty
RUN sh -c ". ${VENV_PATH}/bin/activate"

# Install Shdotenv
#RUN wget "https://github.com/ko1nksm/shdotenv/releases/latest/download/shdotenv" -O "/usr/local/bin/shdotenv"
RUN curl -s "https://github.com/ko1nksm/shdotenv/releases/latest/download/shdotenv" -o "/usr/local/bin/shdotenv"

# Ensure correct Permissions
RUN chmod +x /usr/local/bin/shdotenv

# Set PATH Variable to Include shdotenc
ENV PATH="$PATH:/usr/local/bin"

# Install required Packages
RUN --mount=type=cache,mode=0777,target=/var/lib/pip,sharing=locked \
    pip install --cache-dir /var/lib/pip -r "${APP_PATH}/requirements.txt"

# Change Directory
WORKDIR "${APP_PATH}"

# Run Command
ENTRYPOINT [ "./hah.py" ]
