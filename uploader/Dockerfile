FROM python:3.11

# environemnt variables
ENV RABBITMQ_URI="amqp://guest:guest@localhost:5672/%2F" \
    PREFIX="" \
    CDR_URL="https://api.cdr.land" \
    CDR_TOKEN="" \
    MAX_SIZE=300

WORKDIR /src

COPY requirements.txt /src/
RUN pip install -r /src/requirements.txt

COPY . /src/

CMD python uploader.py
