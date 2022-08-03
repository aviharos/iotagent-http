# iotagent-http

[![License: MIT](https://img.shields.io/github/license/ramp-eu/TTE.project1.svg)](https://opensource.org/licenses/MIT)

A basic IoT agent for connecting Siemens S7-15xx PLCs with the [Fiware Orion Context Broker](https://github.com/telefonicaid/fiware-orion). The IoT agent can also handle IoT devices that can send JSONs over HTTP POST.

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

The Fiware Orion Context Broker uses HTTP connection. The Siemens S7-15xx PLCs' LHTTP Library provides HTTP functionality, but HTTP DELETE is not implemented in the library yet (as of June 2022). This IoT agent recieves HTTP requests from the PLC, translates the HTTP request, then sends it to the Orion Context Broker. The agent waits for the Orion Context Broker's response, and returns that to the IoT device.

## Build
You can build the software using the Dockerfile:

	docker build -t <component>:<version> .

## Usage

The software runs in a docker container. Run component

	docker run -p 8070:8070 <component>:<version>

### Configuration - IoT agent
By default, the component uses port 8070 for communication. You can change this in [conf.py](app/conf.py). There are a few configurations besides changing the port, all of which are related to logging.

### Configuration - PLC
You need to configure the PLC program to send the following data to the IoT agent using LHTTP\_Post. Please note that the following data is sent as raw data, and since the PLC's string variables cannot contain more than 254 characters, the string must not exceed this length. If you use another IoT device where this constraint does not exist, you can send data longer than 254 characters.

	{"url": "http://<orion-host>:<orion-port>/v2/entities",
	"method": <HTTP method>,
	"headers": ["Content-Type: <content-type>"],
	"data": <actual data in JSON or plain text format>}

### Examples
#### DELETE
Sending the following to the IoT agent using HTTP POST

	{"url": "http://orion:1026/v2/entities/urn:ngsi_ld:TrayLoaderStorage:1",
	"method": "DELETE",
	"headers": []
	}	

will have equivalent effect as

	curl --location --request DELETE 'http://localhost:1026/v2/entities/urn:ngsi_ld:TrayLoaderStorage:1'

#### GET
Sending the following to the IoT agent using HTTP POST

	{"url": "http://orion:1026/v2/entities/urn:ngsi_ld:TrayLoaderStorage:1",
	"method": "GET",
	"headers": []
	}

will have equivalent effect as

	curl --location --request GET 'http://localhost:1026/v2/entities/urn:ngsi_ld:TrayLoaderStorage:1'

#### POST
Sending the following to the IoT agent using HTTP POST

	{"url": "http://orion:1026/v2/entities",
	"method": "POST",
	"headers": ["Content-Type: application/json"],
	"data": {
	"type": "TrayLoaderStorage",
	"id": "urn:ngsi_ld:TrayLoaderStorage:1",
	"TrayLoaderStorageCapacity": {"type": "Number", "value": 100},
	"TrayLoaderStorageTrayCounter": {"type": "Number", "value": 100}
	}} 

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

	{"url": "http://orion:1026/v2/entities/urn:ngsi_ld:TrayLoaderStorage:1/attrs/TrayLoaderStorageTrayCounter",
	"method": "PUT",
	"headers": ["Content-Type: application/json"],
	"data": {"value": {"$inc": -1}, "type": "Number"}}

will have equivalent effect as

	curl --location --request PUT 'http://localhost:1026/v2/entities/urn:ngsi_ld:TrayLoaderStorage:1/attrs/TrayLoaderStorageTrayCounter' \
	--header 'Content-Type: application/json' \
	--data-raw '{
	"value": {"$inc": -1},
	"type": "Number"
	}'

## API

The agent does not contain an API.

## Testing

For performing a basic end-to-end test, you have to follow the step below.

	pip install validators
	cd test
	python test_main.py

## Limitations
The IoT agent cannot handle HTTPS and Fiware's authentication system.

## License

The license is not determined yet.
