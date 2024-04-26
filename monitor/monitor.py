#!/usr/bin/env python

import http.server
import json
import logging
import os
import sys
import requests

# ----------------------------------------------------------------------
# WEB SERVER
# ----------------------------------------------------------------------
class MyServer(http.server.SimpleHTTPRequestHandler):
  """
  Handles the responses from the web server. Only response that is
  handled is a GET that will return all known queues.
  """
  def do_GET(self):
    self.path = os.path.basename(self.path)
    if self.path == '':
      self.path = '/'

    if self.path.startswith('queues.json'):
      queues = {}
      try:
        rabbitmq_mgmt_url = os.environ.get('RABBITMQ_MGMT_URL', 'http://rabbitmq:15672')
        rabbitmq_username = os.environ.get('RABBITMQ_USERNAME', 'guest')
        rabbitmq_password = os.environ.get('RABBITMQ_PASSWORD', 'guest')
        response = requests.get(f"{rabbitmq_mgmt_url}/api/queues/%2F", auth=(rabbitmq_username, rabbitmq_password), timeout=5)
        response.raise_for_status()
        for data in response.json():
          if data['name'].endswith(".error"):
            queue = data['name'][:-6]
            consumers = data['consumers']
            messages = None
            unknown = 0
            errors = data['messages']
          elif data['name'].endswith(".unknown"):
            queue = data['name'][:-8]
            consumers = data['consumers']
            messages = None
            unknown = data['messages']
            errors = 0
          else:
            queue = data['name']
            consumers = data['consumers']
            messages = f'{data["messages"]} / {data["messages_unacknowledged"]}'
            unknown = 0
            errors = 0

          if queue in queues:
            if consumers != 0:
              queues[queue]['consumers'] = consumers
            if messages:
              queues[queue]['messages'] = messages
            if errors != 0:
              queues[queue]['errors'] = errors
            if unknown != 0:
              queues[queue]['unknown'] = unknown
          else:
            queues[queue] = {
              'queue': queue,
              'consumers': consumers,
              'messages': messages,
              'unknown': unknown,
              'errors': errors,
            }
      except:
        logging.exception("Error getting queues from RabbitMQ.")
        queues = {}
      self.send_response(200)
      self.send_header('Content-type', 'application/json')
      self.end_headers()
      self.wfile.write(bytes(json.dumps(list(queues.values())), 'utf-8'))
    else:
      super().do_GET()


# ----------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------
if __name__ == "__main__":
  logging.basicConfig(format='%(asctime)-15s [%(threadName)-15s] %(levelname)-7s :'
                              ' %(name)s - %(message)s',
                      level=logging.DEBUG)
  logging.getLogger('requests.packages.urllib3.connectionpool').setLevel(logging.WARN)
  logging.getLogger('urllib3.connectionpool').setLevel(logging.WARN)
  logging.getLogger('pika').setLevel(logging.WARN)

  server = http.server.HTTPServer(("", 9999), MyServer)
  try:
    server.serve_forever()
  except:
    logging.exception("Error in http server")
    sys.exit(1)
  finally:
    server.server_close()
