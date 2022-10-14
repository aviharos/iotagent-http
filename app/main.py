# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""The main file, containing the IoTAgent class 

The IoTAgent is derived from http.server.BaseHTTPRequestHandler
The http.server.HTTPServer class uses the IoTAgent as the handler class 

Credits to mdonkers for the server template:
https://gist.github.com/mdonkers/63e115cc0c79b4f6b8b3a6b797e485c7

Usage:
./main.py
or
python main.py
"""

# Standard Library imports
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import sys

# PyPI imports
import requests
import validators

# custom imports
from Logger import getLogger
from HTTPRequest import HTTPRequest

logger = getLogger(__name__)

PORT = os.environ.get("PORT")
try:
    PORT = int(PORT)
    logger.info(f"Using port: {PORT}")
except:
    PORT = 4315
    logger.warning(f"Failed to convert env var PORT to int. Using default port: {PORT}")

USE_PLUGIN = os.environ.get("USE_PLUGIN")
logger.debug(f"USE_PLUGIN: {USE_PLUGIN}")
if USE_PLUGIN is None:
    USE_PLUGIN = False
elif USE_PLUGIN.lower() == "true":
    USE_PLUGIN = True
else:
    USE_PLUGIN = False
logger.debug(f"USE_PLUGIN: {USE_PLUGIN}")

"""
A function for loading the plugin.transform module

Returns:
    plugin.transform if 
        - USE_PLUGIN environment variable is true (case insensitive) and
        - the plugin.transform module can be imported
    None otherwise
"""
if not USE_PLUGIN:
    transform = None
else:
    try:
        from plugin import transform
        logger.info(f"Transform function imported from plugin")
    except ModuleNotFoundError:
        logger.info(f"No plugin found")
        transform = None
    except (SyntaxError, IndentationError, ImportError):
        logger.error(f"Failed to import transform function from plugin")
        transform = None


class IoTAgent(BaseHTTPRequestHandler):
    """The IoTAgent BaseHTTPRequestHandler class

    The agent is the handler class of the HTTPServer class 

    The agent gets data from the IoT device in raw data
    then extracts the URL,
    the headers and the HTTP method from it. 
    If there is a transform key, it is also extracted.
    The raw data must contain a JSON in string format.

    See the README for a more in-depth explanation.
    """

    def _set_response(self, status_code: int):
        """Set response based on the status_code of the HTTP Request

        Args:
            status_code (int): HTTP status code resulting after the HTTP Request
                is sent to Orion
        """
        logger.info(f"_set_response: status_code == {status_code}")
        self.send_response(status_code)
        self.send_header("Content-type", "text/plain")
        self.end_headers()

    def _handle_bad_request(self, error: Exception):
        """A function for handling bad requests 

        Args:
            error (Exception): the error raised by the internal methods of the IoTAgent
        """
        msg = f'Error processing request.\nTraceback:\n{error}'
        logger.error(msg)
        self._set_response(status_code=400)
        self.wfile.write(msg.encode('utf-8'))

    def _handle_connection_error(self, error: Exception):
        """A function for handling connection errors

        It is invoked when a requests.exceptions.ConnectionError is raised

        Args:
            error (Exception): the error raised
        """
        msg = f'Connection error.\n{type(error).__name__}\nTraceback:\n{error}'
        logger.error(msg)
        self._set_response(503)
        self.wfile.write(msg.encode('utf-8'))

    def _clean_keys(self, parsed_data: dict):
        """Clean keys of the parsed request 

        The cleaning of the keys includes:
            - stripping of whitespace
            - transform to lowercase

        We need to make an iterable of the keys instead of iterating over the keys
        to avoid RuntimeError: dictionary keys changed during iteration

        Args:
            parsed_data (dict): parsed JSON

        Returns:
            parsed_data with keys cleaned 
        """
        keys = tuple(parsed_data.keys())
        for key in keys:
            if key != key.lower().strip():
                parsed_data[key.lower().strip()] = parsed_data[key]
                del parsed_data[key]
        return parsed_data

    def _validate_method(self, parsed_data: dict):
        """Validate the HTTP method of the parsed request

        Args:
            parsed_data (dict): parsed JSON 

        Raises:
            ValueError:
                if the HTTP method is invalid 
            NotImplementedError:
                if the HTTP method is not implemented
        """
        if parsed_data['method'] not in ('GET', 'HEAD', 'POST', 'PUT', 'DELETE',
                                         'CONNECT', 'OPTIONS', 'TRACE'):
            raise ValueError('Not a valid HTTP method: {}'.format(parsed_data['method']))
        if parsed_data['method'] not in ('GET', 'POST', 'PUT', 'DELETE'):
            raise NotImplementedError('Not implemented HTTP method: {}'.format(parsed_data['method']))

    def _validate_mandatory_keys(self, parsed_data: dict):
        """Validate mandatory keys of the parsed request

        Mandatory keys:
            - all requests:
                - url
                - headers
                - method
            - for POST and PUT requests, the following are also mandatory:
                - data

        Riases:
            KeyError:
                If one mandatory key is not present

        Args:
            parsed_data (dict): decoded request
        """
        mandatory_keys = ['url', 'headers', 'method']
        if parsed_data['method'] in ('POST', 'PUT'):
            mandatory_keys.append('data')
        for key in mandatory_keys:
            if key not in parsed_data.keys():
                raise KeyError(f'The decoded json: {parsed_data} does not include the key: \'{key}\'')

    def _validate_headers(self, parsed_data: dict):
        """Validate headers of parsed request

        Raises:
            ValueError:
                if one of the headers consists of 2 or more ":"-s,
                thus having 3 or more separate values

        Args:
            parsed_data (dict): parsed JSON 
        """
        for header in parsed_data['headers']:
            header = str(header)
            split = [x.strip() for x in header.split(':')]
            if len(split) > 2:
                raise ValueError(f'The decoded header: "{header}" does not have a structure of\n"key: value" or "key" or contains more than one ":"')

    def _extract_headers(self, parsed_data: dict):
        """Extract headers from the parsed request, turn them into a dict 

        Args:
            parsed_data (dict): parsed request

        Returns:
            headers (dict): headers parsed in to a dict 
        """
        headers = {}
        for header in parsed_data['headers']:
            header = str(header)
            split = [x.strip() for x in header.split(':')]
            if len(split) == 2:
                name = split[0]
                value = split[1]
                headers[name] = value
            elif len(split) == 1:
                # todo test this case
                name = split[0]
                headers[name] = None
        return headers

    def _validate_url(self, parsed_data: dict):
        """Validate url of the parsed request

        Raises: 
            validators.ValidationFailure 
                if the parsed_data["url"] field is not valid

        Args:
            parsed_data (dict): decoded parsed request 
        """
        validators.url(parsed_data['url'])

    def _validate_content_type(self, parsed_data: dict, headers: dict):
        """Validate the Content-Type and the format of the data field of the parsed request

        Raises:
            ValueError:
                if the Content-Type is missing from the headers
                if the Content-Type header does not contain "application/json" or "text/plain"
                if the Content-Type is "application/json" but the parsed_data["data"] is not a dict
                if the Content-Type is "text/plain" but the length of the parsed_data["data"] is 0

        Args:
            parsed_data (dict): parsed request 
            headers (dict): headers of the request 
        """
        if 'Content-Type' not in headers.keys():
            raise ValueError('Missing header: "Content-Type: application/json" or "Content-Type: text/plain"')
        if headers['Content-Type'] not in ('application/json', 'text/plain'):
            raise ValueError('Unsupported Content-Type: {}\nSupported Content-Types: "application/json", "text/plain"')
        if headers['Content-Type'] == 'application/json':
            if type(parsed_data['data']) is not dict:
                raise ValueError('Content-Type is application/json, but the data does not contain a json: {}'.format(parsed_data['data']))
            data = str(parsed_data['data']).replace('\'', '"')
        if headers['Content-Type'] == 'text/plain':
            # TODO test
            data = parsed_data['data']
            if len(str(data)) == 0:
                raise ValueError('The decoded request has a method {}, but has no data.'.format(parsed_data['method']))

    def _construct_request(self, parsed_data: dict, headers: dict):
        """Construct the HTTPRequest from the parsed request

        Args:
            parsed_data (dict): parsed request  
            headers (dict): request headers

        Returns:
            req (HTTPRequest)
        """
        logger.debug(f'Parsed data:\n{parsed_data}')
        if parsed_data['method'] in ('GET', 'DELETE'):
            req = HTTPRequest(url=parsed_data['url'],
                              transform=parsed_data['transform'] if "transform" in parsed_data else {},
                              method=parsed_data['method'],
                              headers=headers)
            return req
        elif parsed_data['method'] in ('POST', 'PUT'):
            if headers['Content-Type'] == 'application/json':
                data = str(parsed_data['data']).replace('\'', '"').replace('"dinc"', '"$inc"')
            elif headers['Content-Type'] == 'text/plain':
                data = parsed_data['data'].replace('"dinc"', '"$inc"')
            headers['Content-Length'] = str(len(data))
            req = HTTPRequest(url=parsed_data['url'],
                              transform= parsed_data['transform'] if "transform" in parsed_data else {},
                              method=parsed_data['method'],
                              headers=headers,
                              data=data)
            return req

    def _apply_plugin_if_present(self, req: HTTPRequest):
        """Apply plugin if present

        If the plugin is used, transform is plugin.transform,
        if the plugin is not used, transform is None
        The plugin is not a part of the IoTAgent

        Args:
            req (HTTPRequest): request to transform 

        Returns:
            req (HTTPRequest)
        """
        logger.debug(f"transform: {transform}")
        if transform is not None:
            req = transform(req)
            logger.info(f"Request transformed: {req}")
        return req

    def _send_request_to_broker(self, req: HTTPRequest):
        """Manage sending the HTTPRequest to the Orion broker

        Args:
            req (HTTPRequest): request to send 

        Returns:
            res (requests response object): Orion response
        """
        if req.method == 'GET':
            res = requests.get(url=req.url, headers=req.headers)
        elif req.method == 'POST':
            if req.headers['Content-Type'] == 'text/plain':
                res = requests.post(url=req.url, headers=req.headers, data=req.data)
            if req.headers['Content-Type'] == 'application/json':
                res = requests.post(url=req.url, headers=req.headers, json=json.loads(req.data))
        elif req.method == 'PUT':
            if req.headers['Content-Type'] == 'text/plain':
                res = requests.put(url=req.url, headers=req.headers, data=req.data)
            if req.headers['Content-Type'] == 'application/json':
                res = requests.put(url=req.url, headers=req.headers, json=json.loads(req.data))
        elif req.method == 'DELETE':
            res = requests.delete(url=req.url, headers=req.headers)
        res.close()
        return res

    def _prepare_request(self, post_data: str):
        """Prepare request from post_data 

        Raises:
            ValueError:
                if the post_data does not contain a dictionary
            KeyError:
                if the decoded JSON does not contain the key "method"
            Other errors according to the subfunctions used

        Args:
            post_data (str): post_data in bytestring

        Returns:
            req (HTTPRequest): consctucted HTTPRequest
        """
        parsed_data = json.loads(post_data)
        if type(parsed_data) is not dict:
            raise ValueError(f'The sent data does not contain a json:\n{parsed_data}')
        parsed_data = self._clean_keys(parsed_data)
        if 'method' not in parsed_data.keys():
            raise KeyError(f'The decoded json:{parsed_data} does not include the key: "method"')
        parsed_data['method'] = parsed_data['method'].upper().strip()
        self._validate_method(parsed_data)
        self._validate_mandatory_keys(parsed_data)
        parsed_data['url'] = parsed_data['url'].strip()
        self._validate_url(parsed_data)
        self._validate_headers(parsed_data)
        headers = self._extract_headers(parsed_data)
        if parsed_data['method'] in ('POST', 'PUT'):
            self._validate_content_type(parsed_data, headers)
        req = self._construct_request(parsed_data, headers)
        return req

    def _manage_send_request_to_broker(self, req: HTTPRequest):
        """Manage sending request to the broker 

        Sends the request to the broker,
        handles bad requests or connection errors,
        sends response to the IoT device in the case of success

        Args:
            req (HTTPRequest): request to send
        """
        try:
            res = self._send_request_to_broker(req)
        except requests.exceptions.InvalidSchema as error:
            self._handle_bad_request(error)
        except requests.exceptions.ConnectionError as error:
            self._handle_connection_error(error)
        else:
            logger.info(f'Orion response:\n{res}')
            self._set_response(res.status_code)
            self.wfile.write(f'{res.content}'.encode('utf-8'))

    def do_GET(self):
        """HTTP GET functionality, provide healthcheck"""
        logger.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
        self._set_response(200)
        self.wfile.write(f'iotagent-http running.\nPython version: {sys.version}\nvalidators version: {validators.__version__}'.encode('utf-8'))

    def do_POST(self):
        """ Manage HTTP POST functionality 

        Recieve HTTP requests from the IoT devices using HTTP POST
        The requests are then parsed, decoded, sent to the Orion broker,
        then the response is sent back to the IoT agent"""
        # Get the size of data
        content_length = int(self.headers['Content-Length'])
        # Gets the data itself
        post_data = self.rfile.read(content_length)
        logger.info('POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n',
                    str(self.path), str(self.headers), post_data.decode('utf-8'))

        try:
            req = self._prepare_request(post_data)
        except (ValueError,
                KeyError,
                IndexError,
                NotImplementedError,
                validators.ValidationFailure,
                json.JSONDecodeError,
                requests.exceptions.InvalidSchema) as error:
            self._handle_bad_request(error)
        else:
            logger.info(f'Request decoded:\n{req}')
            req = self._apply_plugin_if_present(req)
            self._manage_send_request_to_broker(req)


def run(server_class=HTTPServer, handler_class=IoTAgent):
    server_address = ('', PORT)
    http_service = server_class(server_address, handler_class)
    logger.info(f'Starting PLC IoT agent on port {PORT}...')
    try:
        http_service.serve_forever()
    except KeyboardInterrupt:
        pass
    http_service.server_close()
    logger.info('KeyboardInterrupt. Stopping PLC IoT agent...')


if __name__ == '__main__':
    run()
