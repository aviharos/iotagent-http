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
            raise ValueError(f'The sent raw data does not contain a json:\n{post_data}')

        for key in all_data.keys():
            if key != key.lower().strip():
                all_data[key.lower().strip()] = all_data[key]
                del all_data[key]

        if 'method' not in all_data.keys():
            raise KeyError(f'The decoded json:{all_data} does not include the key: \'method\'')
        all_data['method'] = all_data['method'].upper().strip()
        if all_data['method'] not in ('GET', 'HEAD', 'POST', 'PUT', 'DELETE',
                                      'CONNECT', 'OPTIONS', 'TRACE'):
            raise ValueError('Not a valid HTTP method:{}'.format(all_data['method']))

        if all_data['method'] not in ('GET', 'POST', 'PUT', 'DELETE'):
            raise NotImplementedError('Not implemented HTTP method: {}'.format(all_data['method']))

        mandatory_keys = ['url', 'headers', 'method']
        if all_data['method'] in ('POST', 'PUT'):
            mandatory_keys.append('data')

        for key in mandatory_keys:
            if key not in all_data.keys():
                raise KeyError(f'The decoded json:{all_data} does not include the key: \'{key}\'')

        all_data['url'] = all_data['url'].strip()
        # raise validators.ValidationError if not valid url
        validators.url(all_data['url'])

        logger.debug('Unprocessed headers:\n{}\nType: {}'.format(all_data['headers'], type(all_data['headers'])))

        try:
            headers = {}
            for header in all_data['headers']:
                header = str(header)
                name, value = header.split(':')[0].strip(), header.split(':')[1].strip()
                headers[name] = value
        except IndexError:
            raise IndexError(f'The decoded header: {header} does not have a structure of\nkey: value')

        logger.debug('Processed headers:\n{}'.format(headers))

        if all_data['method'] in ('GET', 'DELETE'):
            req = HTTPRequest(url=all_data['url'],
                              method=all_data['method'],
                              headers=headers)
            return req

        if 'Content-Type' not in headers.keys():
            raise ValueError('Missing header: "Content-Type: application/json" or "Content-Type: text/plain"')

        if headers['Content-Type'] not in ('application/json', 'text/plain'):
            raise ValueError('Unsupported Content-Type: {}\nSupported Content-Types: "application/json", "text/plain"')

        if headers['Content-Type'] == 'application/json':
            if type(all_data['data']) is not dict:
                raise ValueError('Content-Type is application/json, but the data does not contain a json: {}'.format(all_data['data']))
            data_str = str(all_data['data']).replace('\'', '"')
            headers['Content-Length'] = str(len(data_str))
            req = HTTPRequest(url=all_data['url'],
                              method=all_data['method'],
                              headers=headers,
                              data_type='json',
                              data_json=data_str)

        if headers['Content-Type'] == 'text/plain':
            # TODO test
            # now the request must be either POST or PUT, require a body
            data_str = all_data['data']
            headers['Content-Length'] = str(len(data_str))
            if len(data_str) == 0:
                raise ValueError('The decoded request has a method {}, but has no data.'.format(all_data['method']))
            req = HTTPRequest(url=all_data['url'],
                              method=all_data['method'],
                              headers=headers,
                              data_type='raw',
                              data_raw=all_data['data'])
        return req

    def send_request_to_broker(self, req):
        if req.method == 'GET':
            # TODO test
            res = requests.get(url=req.url, headers=req.headers)

        elif req.method == 'POST':
            # TODO test
            if req.data_type == 'raw':
                res = requests.post(url=req.url, headers=req.headers, data=req.data_raw)
            elif req.data_type == 'json':
                res = requests.post(url=req.url, headers=req.headers, data=req.data_json)
                
        elif req.method == 'PUT':
            if req.data_type == 'raw':
                res = requests.put(url=req.url, headers=req.headers, data=req.data_raw)
            elif req.data_type == 'json':
                res = requests.put(url=req.url, headers=req.headers, data=req.data_json)

        elif req.method == 'DELETE':
            # TODO test
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

        try:
            request = self.decode_request(post_data)
        except (ValueError or
                KeyError or
                IndexError or
                NotImplementedError or
                validators.ValidationError or
                json.JSONDecodeError) as error:
            # TODO test
            logger.error(f'Error decoding message. Traceback:\n{error}')
            self.send_response(400)
            self.end_headers()
            self.wfile.write("POST request for {}\nError decoding message.\nTraceback:\n{}".format((self.path).encode('utf-8'), str(error).encode('utf-8')))
        else:
            logger.debug(f'Request decoded:\n{request}')
            res = self.send_request_to_broker(request)
            logger.info(f'Orion response:\n{res}')
            self.send_response(res.status_code)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write("POST request for {}\nOrion status code: {}".format((self.path).encode('utf-8'), str(res.status_code)).encode('utf-8'))


def run(server_class=HTTPServer, handler_class=Server, port=8070):
    server_address = ('', port)
    http_service = server_class(server_address, handler_class)
    logger.info(f'Starting PLC IoT agent server on port {port}...')
    try:
        http_service.serve_forever()
    except KeyboardInterrupt:
        pass
    http_service.server_close()
    logger.info('KeyboardInterrupt. Stopping PLC IoT agent...')


if __name__ == '__main__':
    if len(sys.argv) == 2:
        run(port=int(sys.argv[1]))
    else:
        run()
