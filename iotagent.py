#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
credits to mdonkers for the server template:
https://gist.github.com/mdonkers/63e115cc0c79b4f6b8b3a6b797e485c7

Usage:
./iotagent.py
or
python iotagent.py

The configuration can be set in conf.py

The agent gets data from the IoT device in raw data, then extracts the URL,
the headers and the HTTP method from it.
The raw data must contain a JSON in string format.

Sample payloads:
Post new entity to the Orion broker
{"url": "http://localhost:1026/v2/entities",
"method": "POST",
"headers": ["Content-Type: application/json"],
"data": {
"type": "TrayLoaderStorage",
"id": "urn:ngsi_ld:TrayLoaderStorage:1",
"TrayLoaderStorageCapacity": {"type": "Number", "value": 100},
"TrayLoaderStorageTrayCounter": {"type": "Number", "value": 100}
}}

Change a numeric attribute
{"url": "http://localhost:1026/v2/entities/urn:ngsi_ld:TrayLoaderStorage:1/attrs/TrayLoaderStorageTrayCounter/value",
"method": "PUT",
"headers": ["Content-Type: text/plain"],
"data": "100"}

Get an object from the Orion broker
{"url": "http://localhost:1026/v2/entities/urn:ngsi_ld:TrayLoaderStorage:1",
"method": "GET",
"headers": []
}

Delete an object in the Orion broker
{"url": "http://localhost:1026/v2/entities/urn:ngsi_ld:TrayLoaderStorage:1",
"method": "DELETE",
"headers": []
}

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
    data: str = field(default='')


class IoTAgent(BaseHTTPRequestHandler):
    def _set_response(self, status_code):
        self.send_response(status_code)
        self.send_header("Content-type", "text/plain")
        self.end_headers()

    def _handle_bad_request(self, error):
        msg = f'Error processing request.\n{type(error).__name__}\nTraceback:\n{error}'
        logger.error(msg)
        self._set_response(400)
        self.wfile.write(msg.encode('utf-8'))

    def _handle_connection_error(self, error):
        msg = f'Connection error.\n{type(error).__name__}\nTraceback:\n{error}'
        logger.error(msg)
        self._set_response(503)
        self.wfile.write(msg.encode('utf-8'))

    def decode_request(self, post_data):
        all_data = json.loads(post_data)
        if type(all_data) is not dict:
            raise ValueError(f'The sent data does not contain a json:\n{post_data}')

        for key in all_data.keys():
            if key != key.lower().strip():
                all_data[key.lower().strip()] = all_data[key]
                del all_data[key]

        if 'method' not in all_data.keys():
            raise KeyError(f'The decoded json:{all_data} does not include the key: \'method\'')
        all_data['method'] = all_data['method'].upper().strip()
        if all_data['method'] not in ('GET', 'HEAD', 'POST', 'PUT', 'DELETE',
                                      'CONNECT', 'OPTIONS', 'TRACE'):
            raise ValueError('Not a valid HTTP method: {}'.format(all_data['method']))

        if all_data['method'] not in ('GET', 'POST', 'PUT', 'DELETE'):
            raise NotImplementedError('Not implemented HTTP method: {}'.format(all_data['method']))

        mandatory_keys = ['url', 'headers', 'method']
        if all_data['method'] in ('POST', 'PUT'):
            mandatory_keys.append('data')

        for key in mandatory_keys:
            if key not in all_data.keys():
                raise KeyError(f'The decoded json: {all_data} does not include the key: \'{key}\'')

        all_data['url'] = all_data['url'].strip()
        # raise validators.ValidationError if not valid url
        validators.url(all_data['url'])

        headers = {}
        for header in all_data['headers']:
            header = str(header)
            split = [x.strip() for x in header.split(':')]
            if len(split) > 2:
                raise ValueError(f'The decoded header: "{header}" does not have a structure of\n"key: value" or "key" or contains more than one ":"')
            elif len(split) == 2:
                name = split[0]
                value = split[1]
                headers[name] = value
            elif len(split) == 1:
                # todo test this case
                name = split[0]
                headers[name] = None

        if all_data['method'] in ('GET', 'DELETE'):
            req = HTTPRequest(url=all_data['url'],
                              method=all_data['method'],
                              headers=headers)
            return req

        # now the request must be either POST or PUT, require content
        if 'Content-Type' not in headers.keys():
            raise ValueError('Missing header: "Content-Type: application/json" or "Content-Type: text/plain"')

        if headers['Content-Type'] not in ('application/json', 'text/plain'):
            raise ValueError('Unsupported Content-Type: {}\nSupported Content-Types: "application/json", "text/plain"')

        if headers['Content-Type'] == 'application/json':
            if type(all_data['data']) is not dict:
                raise ValueError('Content-Type is application/json, but the data does not contain a json: {}'.format(all_data['data']))
            data = str(all_data['data']).replace('\'', '"')

        if headers['Content-Type'] == 'text/plain':
            # TODO test
            data = all_data['data']
            if len(data) == 0:
                raise ValueError('The decoded request has a method {}, but has no data.'.format(all_data['method']))

        headers['Content-Length'] = str(len(data))
        req = HTTPRequest(url=all_data['url'],
                          method=all_data['method'],
                          headers=headers,
                          data=data)
        return req

    def send_request_to_broker(self, req):
        if req.method == 'GET':
            # TODO test
            res = requests.get(url=req.url, headers=req.headers)

        elif req.method == 'POST':
            # TODO test
            res = requests.post(url=req.url, headers=req.headers, data=req.data)
                
        elif req.method == 'PUT':
            res = requests.put(url=req.url, headers=req.headers, data=req.data)

        elif req.method == 'DELETE':
            # TODO test
            res = requests.delete(url=req.url, headers=req.headers)

        res.close()
        return res

    def do_GET(self):
        #TODO test
        logger.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
        self._set_response(200)
        self.wfile.write(f'PLC IoT agent running.\nPython version: {sys.version}\validators version: {validators.__version__}'.encode('utf-8'))

    def do_POST(self):
        # Get the size of data
        content_length = int(self.headers['Content-Length'])
        # Gets the data itself
        post_data = self.rfile.read(content_length)
        logger.info('POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n',
                    str(self.path), str(self.headers), post_data.decode('utf-8'))

        try:
            request = self.decode_request(post_data)
        except (ValueError,
                KeyError,
                IndexError,
                NotImplementedError,
                validators.ValidationFailure,
                json.JSONDecodeError,
                requests.exceptions.InvalidSchema) as error:
            self._handle_bad_request(error)
        else:
            logger.info(f'Request decoded:\n{request}')
            try:
                res = self.send_request_to_broker(request)
            except (requests.exceptions.InvalidSchema,
                    requests.exceptions.ConnectionError) as error:
                if type(error) == requests.exceptions.InvalidSchema:
                    self._handle_bad_request(error)
                elif type(error) == requests.exceptions.ConnectionError:
                    self._handle_connection_error(error)
            else:
                logger.info(f'Orion response:\n{res}')
                self._set_response(res.status_code)
                # TODO test
                self.wfile.write(f'Orion response:\nstatus code: {res.status_code}\nResponse content:\n{res.content}'.encode('utf-8'))


def run(server_class=HTTPServer, handler_class=IoTAgent, port=conf['port']):
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
    run()
