FROM python:3.11

WORKDIR /app
EXPOSE 8080

ENV PYTHONUNBUFFERED=1 \
    SYSTEM_NAME="ncsa" \
    SYSTEM_VERSION="0.2.0" \
    CDR_TOKEN="" \
    CDR_KEEP_EVENT="no" \
    CALLBACK_SECRET="this_is_a_really_silly_secret" \
    CALLBACK_URL="" \
    CALLBACK_USERNAME="" \
    CALLBACK_PASSWORD="" \
    RABBITMQ_URI="amqp://guest:guest@localhost:5672/%2F"

COPY requirements.txt ./
RUN pip install -r ./requirements.txt

COPY * .
ENTRYPOINT ["python", "server.py"]
