FROM python:3.13-slim
LABEL author="IoT-OpenThread-Team from the winter term 2024/2025 at the FH Dortmund"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN groupadd -r coap-server && useradd -r -g coap-server coap-server
USER coap-server

# RUN mkdir -p /usr/src/coap-server
WORKDIR /usr/src/coap-server
COPY * ./

# port needed for CoAP protocol
EXPOSE 5683

# launch the CoAP-server
CMD ["python", "-m", "coap-server"]
# CMD ["python", "-m", "mqtt_client"] # To test the basic mqtt broker
