FROM python:3.11

WORKDIR /app
EXPOSE 8080

ARG VERSION="unknown"
ENV PYTHONUNBUFFERED=1 \
    SYSTEM_NAME="ncsa" \
    SYSTEM_VERSION="${VERSION}" \
    CDR_TOKEN="" \
    CDR_KEEP_EVENT="no" \
    CALLBACK_SECRET="this_is_a_really_silly_secret" \
    CALLBACK_URL="" \
    CALLBACK_USERNAME="" \
    CALLBACK_PASSWORD="" \
    RABBITMQ_URI="amqp://guest:guest@localhost:5672/%2F" \
    PREFIX=""

VOLUME /data

# setup packages needed
#    apt-get -y install python3-gdal libgdal-dev libgl1 && \
RUN apt-get update && \
    apt-get -y install python3-gdal libgdal-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install -r ./requirements.txt

COPY * .
ENTRYPOINT ["python", "server.py"]
