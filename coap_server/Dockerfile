# Base image: Using official Python slim image for smaller size
FROM python:3.13-slim

# Image metadata
LABEL title="CoAP 2 MQTT Bridge"
LABEL author="IoT-OpenThread-Team from the winter term 2024/2025 at the FH Dortmund"

# Set working directory
WORKDIR /usr/src/coap-server

# Install dependencies from requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user for security
RUN groupadd -r coap-server && useradd -r -g coap-server coap-server

# Copy application files
COPY * ./

# Switch to non-root user
USER coap-server

# CoAP protocol port
EXPOSE 5683

# Start CoAP server
CMD ["python", "-m", "coap_server"]
