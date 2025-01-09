FROM python:3.13-slim
LABEL title="CoAP 2 MQTT Bridge"
LABEL author="IoT-OpenThread-Team from the winter term 2024/2025 at the FH Dortmund"

COPY requirements_minimal.txt .
RUN pip install --no-cache-dir -r requirements_minimal.txt

RUN groupadd -r coap-server && useradd -r -g coap-server coap-server
USER coap-server

# RUN mkdir -p /usr/src/coap-server
WORKDIR /usr/src/coap-server
COPY * ./

# port needed for CoAP protocol
EXPOSE 5683

# launch the CoAP-server
# - ??
CMD ["python", "-m", "coap_server"]

# To test the basic mqtt broker
# CMD ["python", "-m", "periodical_mqtt_client"]
