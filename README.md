# iotagent-plc

A basic IoT agent for connecting Siemens S7-15xx PLCs with the [Fiware Orion Context Broker](https://github.com/telefonicaid/fiware-orion). The IoT agent can also handle IoT devices that can send JSONs over HTTP POST.

## Contents

- [iotagent-plc](#title)
  - [Contents](#contents)
  - [Background](#background)
  - [Install](#install)
  - [Usage](#usage)
  - [API](#api)
  - [Testing](#testing)
  - [License](#license)

## Background

The Fiware Orion Context Broker uses HTTP connection. The Siemens S7-15xx PLCs' LHTTP Library provides HTTP functionality, but one cannot specify headers freely. Also, HTTP PUT and DELETE are not implemented in the library. This IoT agent recieves HTTP requests from the PLC, translates the HTTP request, then sends it to the Orion Context Broker. The agent waits for the Orion Context Broker's response, and returns that to the IoT device.

## Install
The component is available as a docker image. You can build it using the Dockerfile:

	docker build -t <component>:<version> .

## Usage

Run component

	docker run -p 8070:8070 <component>:<version>

### Configuration - IoT agent
By default, the component uses port 8070 for communication. You can change this in [conf.py](app/conf.py). There is no configuration besides changing the port.

### Configuration - PLC
You need to configure the PLC program to send the following data to the IoT agent using LHTTP\_Post.

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

will be translated to the equivalent of

	curl --location --request DELETE 'http://localhost:1026/v2/entities/urn:ngsi_ld:TrayLoaderStorage:1'

#### GET
Sending the following to the IoT agent using HTTP POST

	{"url": "http://orion:1026/v2/entities/urn:ngsi_ld:TrayLoaderStorage:1",
	"method": "GET",
	"headers": []
	}

will be translated to the equivalent of

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

will be translated to the equivalent of

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

will be translated to the equivalent of

	curl --location --request PUT 'http://localhost:1026/v2/entities/urn:ngsi_ld:TrayLoaderStorage:1/attrs/TrayLoaderStorageTrayCounter' \
	--header 'Content-Type: application/json' \
	--data-raw '{
	"value": {"$inc": -1},
	"type": "Number"
	}'

## API

The agent does not contain an API.

## Testing

The tests are yet to be written.

For performing a basic end-to-end test, you have to follow the step below.

	pip install validators
	python test/test_main.py


## License

No license yet.
