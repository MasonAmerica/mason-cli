FROM python:2.7-slim

# Create non-root user
RUN useradd -ms /bin/bash masoncli

# Set working directory
WORKDIR /app

# Copy source
COPY . /app

# Install dependencies and mason-cli
RUN pip install .

# Switch to masoncli user
WORKDIR /home/masoncli
USER masoncli

# Run mason cli
ENTRYPOINT ["/usr/local/bin/mason"]
