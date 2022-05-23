#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
credits to mdonkers for the server template:
https://gist.github.com/mdonkers/63e115cc0c79b4f6b8b3a6b797e485c7

Usage:
./server.py port
or
./server.py
In the latter case, port 8070 is used.

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
import validators

# custom imports
from conf import conf

log_levels = {'DEBUG': logging.DEBUG,
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
    method: str = field(default='GET')
    data_type: str = field(default='no_data')  # or 'json' or 'no_data'
    data_json: dict = field(default_factory={})
    data_raw: str = field(default='')


class Server(BaseHTTPRequestHandler):
    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def decode_request(self, post_data):
        all_data = json.loads(post_data)
        if type(all_data) is not dict:
            raise ValueError(f'Error.\nThe sent raw data does not contain a json:\n{post_data}')

        for key in all_data.keys():
            if key != key.lower().strip():
                all_data[key.lower().strip()] = all_data[key]
                del all_data[key]

        if 'method' not in all_data.keys():
            raise KeyError(f'Error.\nThe decoded json:{all_data} does not include the key: \'method\'')
        all_data['method'] = all_data['method'].upper().strip()
        if all_data['method'] not in ('GET', 'HEAD', 'POST', 'PUT', 'DELETE',
                                      'CONNECT', 'OPTIONS', 'TRACE'):
            raise ValueError('Error.\nNot a valid HTTP method:{}'.format(all_data['method']))

        if all_data['method'] not in ('GET', 'POST', 'PUT', 'DELETE'):
            raise NotImplementedError('Not implemented HTTP method: {}'.format(all_data['method']))

        mandatory_keys = ['url', 'headers', 'method']
        if all_data['method'] in ('POST', 'PUT'):
            mandatory_keys.append('data')

        for key in mandatory_keys:
            if key not in all_data.keys():
                raise KeyError(f'Error.\nThe decoded json:{all_data} does not include the key: \'{key}\'')

        all_data['url'] = all_data['url'].strip()
        # raise validators.ValidationError if not valid url
        validators.url(all_data['url'])

        try:
            headers = {}
            for header in all_data[headers]:
                header = str(header)
                name, value = header.split(':')[0].strip(), header.split(':')[1].strip()
                headers[name] = value
        except IndexError:
            raise IndexError(f'The decoded header: {header} does not have a structure of\nkey: value')

        if all_data['method'] in ('GET', 'DELETE'):
            req = HTTPRequest(url=all_data['url'],
                              method=all_data['method'],
                              headers=headers)
            return req

        try:
            data_json = json.loads(all_data['data'])
        except json.JSONDecodeError:
            data_raw = all_data['data']
            # now the request must be either POST or PUT, require a body
            if len(data_raw) == 0:
                raise ValueError('Error.\nThe decoded request has a method {}, but has no data.'.format(all_data['method']))

            req = HTTPRequest(url=all_data['url'],
                              method=all_data['method'],
                              headers=headers,
                              data_type='raw',
                              data_raw=data_raw)
        else:
            req = HTTPRequest(url=all_data['url'],
                              method=all_data['method'],
                              headers=headers,
                              data_type='json',
                              data_json=data_json)
        return req

    def send_request_to_broker(self, req):
        if req.method == 'GET':
            res = requests.get(url=req.url, headers=req.headers)

        elif req.method == 'POST':
            if req.data_type == 'raw':
                res = requests.post(url=req.url, headers=req.headers, data_raw=req.data_raw)
            elif req.data_type == 'json':
                res = requests.post(url=req.url, headers=req.headers, data_json=req.data_json)
                
        elif req.method == 'PUT':
            if req.data_type == 'raw':
                res = requests.put(url=req.url, headers=req.headers, data_raw=req.data_raw)
            elif req.data_type == 'json':
                res = requests.put(url=req.url, headers=req.headers, data_json=req.data_json)

        elif req.method == 'DELETE':
            res = requests.delete(url=req.url, headers=req.headers)

        res.close()
        return res

    def do_GET(self):
        logger.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
        self._set_response()
        self.wfile.write("GET request for {}".format(self.path).encode('utf-8'))

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])  # <--- Gets the size of data
        post_data = self.rfile.read(content_length)  # <--- Gets the data itself
        logger.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
                    str(self.path), str(self.headers), post_data.decode('utf-8'))

        self._set_response()
        try:
            request = self.decode_request(post_data)
        except (ValueError or
                KeyError or
                IndexError or
                NotImplementedError or
                validators.ValidationError or
                json.JSONDecodeError) as error:
            logger.error(f'Error decoding message. Traceback:\n{error}')
            self.wfile.write("POST request for {}\nError decoding message.\nTraceback:\n{}".format((self.path).encode('utf-8'), error))
        else:
            logger.debug(f'Request decoded:\n{request}')
            res = self.send_request_to_broker(request)
            self.wfile.write("POST request for {}\nOrion response:{}".format((self.path).encode('utf-8'), res))


def run(server_class=HTTPServer, handler_class=Server, port=8070):
    server_address = ('', port)
    http_service = server_class(server_address, handler_class)
    logger.info(f'Starting http server on port {port}...')
    try:
        http_service.serve_forever()
    except KeyboardInterrupt:
        pass
    http_service.server_close()
    logger.info('KeyboardInterrupt. Stopping http server...')


if __name__ == '__main__':
    if len(sys.argv) == 2:
        run(port=int(sys.argv[1]))
    else:
        run()
