# iotagent-http

[![License: MIT](https://img.shields.io/github/license/ramp-eu/TTE.project1.svg)](https://opensource.org/licenses/MIT)

A basic IoT agent for connecting HTTP compatible IoT devices with the [Fiware Orion Context Broker](https://github.com/telefonicaid/fiware-orion). Siemens S7-15xx and some of the S7-12xx PLCs are possible IoT devies to be used with the IoT agent.

## Contents

- [iotagent-http](#title)
  - [Contents](#contents)
  - [Background](#background)
  - [Build](#build)
  - [Usage](#usage)
  - [API](#api)
  - [Testing](#testing)
  - [Limitations](#limitations)
  - [License](#license)

## Background

The Fiware Orion Context Broker uses HTTP connection. The Siemens S7-15xx and S7-12xx PLCs' LHTTP Library provides HTTP functionality, but HTTP DELETE is not implemented in the library yet (as of June 2022). The LHTTP library does not natively support sending JSON objects over HTTP (as of August 2022) (note: there is a PLC library for serializing and deserializing JSON objects). This IoT agent recieves HTTP requests from the PLC in string format (`Content-Type: text/plain`), loads the JSON contained in the string, translates it to an HTTP request, then sends it to the Orion Context Broker. The agent waits for the Orion Context Broker's response, and returns that to the IoT device.

## Build
You can build the software using the Dockerfile:

	docker build -t iotagent-http:<version> .

## Usage

The [docker-compose.yml](docker-compose.yml) file shows an example of running the microservice as a docker container.

### Configuration - IoT agent
By default, the component uses port 4315 for communication. You can change this in [docker-compose.yml](docker-compose.yml). There are a few configurations besides changing the port, most of which are related to logging.

The IoT agent can be extended with a plugin. If you wish to use your own plugin, set the `USE_PLUGIN` environment variable to "true".

### Configuration - PLC
You need to configure the PLC program to send the data using the template below to the IoT agent using LHTTP\_PostPut in string format (HTTP POST request). Please note that the following data is sent as raw data, and since the PLC's string variables cannot contain more than 254 characters, the string must not exceed this length. If the data exceeds this limit, an Array of Chars must be used. However, this is not a limitation of the IoT agent. If you use an IoT device where this constraint does not exist, you can send data of arbitrary length.

Sample data (string):

	'{"url": "http://<orion-host>:<orion-port>/v2/entities",
	"method": <HTTP method>,
	"headers": ["Content-Type: <content-type>"],
	"data": <actual data in JSON or plain text format>}'

#### Reserved keywords
You cannot use the keyword `'"dinc"'`. Any instance of `'"dinc"'` will be translated to `'"$inc"'`.

### Examples
#### DELETE
Sending the following to the IoT agent using HTTP POST

	'{"url": "http://orion:1026/v2/entities/urn:ngsi_ld:TrayLoaderStorage:1",
	"method": "DELETE",
	"headers": []
	}'

will have equivalent effect as

	curl --location --request DELETE 'http://localhost:1026/v2/entities/urn:ngsi_ld:TrayLoaderStorage:1'

#### GET
Sending the following to the IoT agent using HTTP POST

	'{"url": "http://orion:1026/v2/entities/urn:ngsi_ld:TrayLoaderStorage:1",
	"method": "GET",
	"headers": []
	}'

will have equivalent effect as

	curl --location --request GET 'http://localhost:1026/v2/entities/urn:ngsi_ld:TrayLoaderStorage:1'

#### POST
Sending the following to the IoT agent using HTTP POST

	'{"url": "http://orion:1026/v2/entities",
	"method": "POST",
	"headers": ["Content-Type: application/json"],
	"data": {
	"type": "TrayLoaderStorage",
	"id": "urn:ngsi_ld:TrayLoaderStorage:1",
	"TrayLoaderStorageCapacity": {"type": "Number", "value": 100},
	"TrayLoaderStorageTrayCounter": {"type": "Number", "value": 100}
	}}'

will have equivalent effect as

	curl --location --request POST 'http://localhost:1026/v2/entities' \
	--header 'Content-Type: application/json' \
	--data-raw '{
	"type": "TrayLoaderStorage",
	"id": "urn:ngsi_ld:TrayLoaderStorage:1",
	"TrayLoaderStorageCapacity": {"type": "Number", "value": 100},
	"TrayLoaderStorageTrayCounter": {"type": "Number", "value": 100}
	}'

#### PUT
Sending the following to the IoT agent using HTTP POST

	'{"url": "http://orion:1026/v2/entities/urn:ngsi_ld:TrayLoaderStorage:1/attrs/TrayLoaderStorageTrayCounter",
	"method": "PUT",
	"headers": ["Content-Type: application/json"],
	"data": {"value": {"$inc": -1}, "type": "Number"}}'

will have equivalent effect as

	curl --location --request PUT 'http://localhost:1026/v2/entities/urn:ngsi_ld:TrayLoaderStorage:1/attrs/TrayLoaderStorageTrayCounter' \
	--header 'Content-Type: application/json' \
	--data-raw '{
	"value": {"$inc": -1},
	"type": "Number"
	}'

## API - plugin support

The agent does not contain an API, but it supports custom plugins. Plugins are disabled by default. You can enable it by writing your own plugin and setting `USE_PLUGIN` to "true" in the [docker-compose.yml](docker-compose.yml).

You can write your own plugin. If the `USE_PLUGIN` environment variable is set to "true", the agent will try to load `plugin.transform` in the `app` directory. If it succeeds, the plugin will be used.

If the `USE_PLUGIN` environment variable does not equal "true" or the agent cannot import `plugin.transform` in the `app` directory, the plugin is not used.

The plugin must take an [HTTPRequest object](app/HTTPRequest.py) as the input, and return an HTTPRequest object. The plugin logic is up to the user. If the plugin needs other python packages, they need to be added to the [requirements.txt](requirements.txt). 

The IoT Agent supports an optional field in the JSON object received that can be used with the plugin. The "transform" field is not used normally, but the agent will extract its value and add it to the HTTPRequest object. If the plugin is not used, the "transform" field is also not used by the agent. But if the user uses a plugin and wants to provide additional information to it, any data can be included in the "transform" field as a JSON.

For example, the following is a valid request:

    {
        "url": "http://orion:1026/v2/entities",
        "method": "PUT",
        "headers": [],
        "data": null,
        "transform": {
            "ws": "urn:ngsi_ld:Workstation:1",
            "ct": "good",
            "cv": 14,
        }
    }

This way, the IoT device can pass additonal information to the plugin in the "transform" field.

## Testing

For performing a basic end-to-end test, you have to follow the steps below.

	pip install -r requirements.txt
	cd test
    docker-compose up -d
	python test_main.py
    docker-compose down

Also, since some parts of the code are hard to test while not running, you shoud test the agent's functionality after running it in a docker container.

    cd ..  # enter the repository's main directory
    docker build -t iotagent-http:latest .
    docker-compose up -d
	cd test/test_requests
	test_iotagent-http_connection.sh  # 1
	create_storage.sh
	get_storage.sh  # 2
	decrement_storage_counter.sh
	get_storage.sh  # 3
	delete_storage.sh
	get_storage.sh  # 4
    docker-compose down

After command #1, you should see a status message of the agent. After command #2, you should see the created storage. After command #3, you should see that the storage's counter is decremented by 1. After #4, you should get an error message - the storage object is deleted.

## Limitations
The IoT agent cannot handle HTTPS and Fiware's authentication system.

## License

[MIT license](LICENSE)

The Robo4Toys TTE does not hold any copyright of any FIWARE or 3rd party software.

