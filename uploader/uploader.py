import json
import logging
import os
import pika
import requests
from requests.exceptions import RequestException
import threading

# rabbitmq uri
rabbitmq_uri = os.getenv("RABBITMQ_URI", "amqp://guest:guest@localhost:5672/%2F")

# prefix for the queue names
prefix = os.getenv("PREFIX", "")

# CDR url, token and max size for upload (in MB)
cdr_url = "https://api.cdr.land"
cdr_token = os.getenv("CDR_TOKEN", "")
max_size = int(os.getenv("MAX_SIZE", "300"))


class Worker(threading.Thread):
    def process(self, method, properties, body):
        self.method = method
        self.properties = properties
        self.body = body
        self.exception = None
        self.result = None

    def run(self):
        try:
            data = json.loads(self.body)
            file = os.path.join("/output", data['cdr_output'])
            logging.debug(f"Uploading data for {data['cog_id']} from {file}")
            # only upload if less than certain size
            if os.path.getsize(file) > max_size * 1024 * 1024:  # size in bytes
                raise ValueError(f"File {file} is larger than {max_size}MB, skipping upload.")
            headers = {'Authorization': f'Bearer {cdr_token}', 'Content-Type': 'application/json'}
            response = requests.post(f'{cdr_url}/v1/maps/publish/features', data=open(file, rb), headers=headers)
            response.raise_for_status()
            result = response.text
        except RequestException as e:
            logging.exception(f"Request Error {response.text}.")
            self.exception = e
        except Exception as e:
            logging.exception("Error processing pipeline request.")
            self.exception = e


def main():
    """
    Main function that connects to rabbitmq and processes messages.
    """
    # connect to rabbitmq
    parameters = pika.URLParameters(rabbitmq_uri)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    # create queues
    channel.queue_declare(queue=f"{prefix}upload", durable=True)
    channel.queue_declare(queue=f"{prefix}upload.error", durable=True)
    channel.queue_declare(queue=f"{prefix}completed", durable=True)

    # listen for messages and stop if nothing found after 5 minutes
    channel.basic_qos(prefetch_count=1)

    # create generator to fetch messages
    consumer = channel.consume(queue=f"{prefix}upload", inactivity_timeout=1)

    # loop getting new messages
    worker = None
    while True:
        method, properties, body = next(consumer)
        if method:
            worker = Worker()
            worker.process(method, properties, body)
            worker.start()
        if worker:
            if not worker.is_alive():
                data = json.loads(worker.body)
                if worker.exception:
                    data['exception'] = repr(worker.exception)
                    channel.basic_publish(exchange='', routing_key=f"{prefix}upload.error", body=json.dumps(data), properties=worker.properties)
                else:
                    logging.info(f"Finished all processing steps for map {data['cog_id']}")
                    data['result'] = worker.result
                    channel.basic_publish(exchange='', routing_key=f"{prefix}completed", body=json.dumps(data), properties=worker.properties)
                channel.basic_ack(delivery_tag=worker.method.delivery_tag)
                worker = None


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)-15s [%(threadName)-15s] %(levelname)-7s :'
                               ' %(name)s - %(message)s',
                        level=logging.INFO)
    logging.getLogger('requests.packages.urllib3.connectionpool').setLevel(logging.WARN)
    logging.getLogger('urllib3.connectionpool').setLevel(logging.WARN)
    logging.getLogger('pika').setLevel(logging.WARN)

    main()
