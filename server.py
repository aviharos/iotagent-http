# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
credits to mdonkers for the server template:
https://gist.github.com/mdonkers/63e115cc0c79b4f6b8b3a6b797e485c7

Usage:
./server.py host port
or
./server.py
In the latter case, localhost and port 8070 is used.

The agent gets data from the IoT device in raw data, then extracts the URL,
the headers and the HTTP method from it.
The raw data must contain a JSON in string format.

Sample payload:
{"url": " http://localhost:1026/v2/entities/urn:ngsi_ld:TrayLoaderStorage:1/attrs/TrayLoaderStorageTrayCounter/value",
"method": "PUT",
"headers": ["Content-Type: text/plain"],
"data": "100"}
"""

# Standard Library imports
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import logging
import requests
import sys

# PyPI imports
# custom imports
from conf import conf

log_levels={'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL}
logger = logging.getLogger(__name__)
formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')
logger.setLevel(log_levels[conf['logging_level']])
if conf['log_to_file']:
    file_handler = logging.FileHandler('iotagent_plc.log')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
if conf['log_to_stdout']:
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

@dataclass
class HTTPRequest:
    url: str
    headers: dict
    method: str = field(default='POST')
    type_: str = field(default='raw') # or 'json'
    data_json: dict = field(default_factory={})
    data_raw: str = field(default='')

class Server(BaseHTTPRequestHandler):
    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def decode_request(self, post_data):
        all_data = json.loads(post_data)
        headers = {x.split(':')[0].strip(): x.split(':')[1].strip() for x in all_data['headers']}
        try:
            data_json = json.loads(all_data['data'])
            request = HTTPRequest(url=all_data['url'], headers=headers, type_='json', data_json=data_json)
        except json.JSONDecodeError:
            data_raw = all_data['data']
            request = HTTPRequest(url=all_data['url'], headers=headers, type_='raw', data_raw=data_raw)
        return request
    
    def send_request_to_broker(self, request):
        if request.method == 'POST':
            pass
        elif request.method == 'PUT':
            requests.put(url=request.url, headers=request.headers, json=request.json)
        elif request.method == 'DELETE':
            pass

    def do_GET(self):
        logger.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
        self._set_response()
        self.wfile.write("GET request for {}".format(self.path).encode('utf-8'))

    def do_POST(self):
        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        post_data = self.rfile.read(content_length) # <--- Gets the data itself
        logger.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
                str(self.path), str(self.headers), post_data.decode('utf-8'))

        self._set_response()
        self.wfile.write("POST request for {}".format(self.path).encode('utf-8'))
        request = self.decode_request(post_data)
        try:
            logger.debug(f'Request decoded:\n{request}')
        except ValueError or KeyError as error:
            logger.error(f'Error decoding message. Traceback:\n{error}')
        self.send_request_to_broker(request)

def run(server_class=HTTPServer, handler_class=Server, address='', port=8070):
    server_address = (address, port)
    http_service = server_class(server_address, handler_class)
    logger.info(f'Starting http server on address {address} on port {port}...')
    try:
        http_service.serve_forever()
    except KeyboardInterrupt:
        pass
    http_service.server_close()
    logger.info('KeyboardInterrupt. Stopping http server...')

if __name__ == '__main__':
    if len(sys.argv) == 3:
        run(address=sys.argv[1], port=int(sys.argv[2]))
    else:
        run()
