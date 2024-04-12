FROM python:3.11

EXPOSE 9999

# environemnt variables
ENV RABBITMQ_MGMT_URL="http://rabbitmq:15672" \
    RABBITMQ_USERNAME="guest" \
    RABBITMQ_PASSWORD="guest"

WORKDIR /src

COPY requirements.txt /src/
RUN pip install -r /src/requirements.txt

COPY . /src/

CMD python monitor.py
