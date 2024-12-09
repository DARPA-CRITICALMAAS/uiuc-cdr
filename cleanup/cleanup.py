import os
import pika
import json
import logging
from time import sleep

# rabbitmq uri
rabbitmq_uri = os.getenv("RABBITMQ_URI", "amqp://guest:guest@localhost:5672/%2F")

# prefix for the queue names
RABBITMQ_QUEUE_PREFIX = os.getenv("PREFIX", "")
INPUT_QUEUE = f"{RABBITMQ_QUEUE_PREFIX}cleanup"
ERROR_QUEUE = f"{RABBITMQ_QUEUE_PREFIX}cleanup.error"
OUTPUT_QUEUE = f"{RABBITMQ_QUEUE_PREFIX}finished"

def parse_command_line():
    import argparse
    parser = argparse.ArgumentParser(description='Cleanup service')
    parser.add_argument('--data-dir', type=str, default='/data', help='Directory where the data is stored')
    parser.add_argument('--output-dir', type=str, default='/output', help='Directory where the output is stored')
    return parser.parse_args()

def main(args):
    # connect to rabbitmq
    logging.info('Connecting to RabbitMQ server')
    parameters = pika.URLParameters(rabbitmq_uri)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    # create queues
    channel.queue_declare(queue=INPUT_QUEUE, durable=True)
    channel.queue_declare(queue=ERROR_QUEUE, durable=True)
    channel.queue_declare(queue=OUTPUT_QUEUE, durable=True)

    # listen for messages and stop if nothing found after 5 minutes
    channel.basic_qos(prefetch_count=1)

    # create generator to fetch messages
    consumer = channel.consume(queue=INPUT_QUEUE, inactivity_timeout=1)

    # loop getting new messages
    running = True
    while running:
        activity = False
        # Take next message from the queue
        method, properties, body = next(consumer)

        if method is not None:
            activity = True
            data = json.loads(body)
            image_path = os.path.join(args.data_dir, data['image_filename'])
            cdr_json_path = os.path.join(args.data_dir, data['json_filename'])
            uiuc_json_path = os.path.join(args.output_dir, data['cdr_output'])
            map_name = os.path.splitext(os.path.basename(image_path))[0]
            logging.debug(f'Cleaning up - {map_name}')

            # Delete files
            try:
                os.remove(image_path)
                os.remove(cdr_json_path)
                os.remove(uiuc_json_path)
            except Exception as e:
                # Send to error queue
                logging.error(f'Error deleting files for map {map_name}: {e}')

                channel.basic_publish(exchange='', routing_key=ERROR_QUEUE, body=body, properties=properties)
                channel.basic_ack(delivery_tag=method.delivery_tag)
            
            # Send to output queue
            channel.basic_publish(exchange='', routing_key=OUTPUT_QUEUE, body=body, properties=properties)
            channel.basic_ack(delivery_tag=method.delivery_tag)

        if not activity:
            sleep(0.5)             
        

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)-15s [%(threadName)-15s] %(levelname)-7s :'
                               ' %(name)s - %(message)s',
                        level=logging.INFO)
    logging.getLogger('pika').setLevel(logging.WARN)

    args = parse_command_line()
    main(args)