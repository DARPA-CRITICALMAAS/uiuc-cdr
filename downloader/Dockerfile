FROM python:3.11

# environemnt variables
ENV RABBITMQ_URI="amqp://guest:guest@localhost:5672/%2F" \
    PREFIX="" \
    CDR_TOKEN="" \
    MAX_SIZE=300

WORKDIR /src
VOLUME /data

COPY requirements.txt /src/
RUN pip install -r /src/requirements.txt

COPY . /src/

CMD python CM_B_downloader.py
