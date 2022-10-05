curl --location --request POST 'localhost:4315' \
--header 'Content-Type: text/plain' \
--data-raw '{"url": "http://orion:1026/v2/entities/urn:ngsi_ld:Storage:1/attrs/Counter",
"method": "PUT",
"headers": ["Content-Type: application/json"],
"data": {"value": {"dinc": -1}, "type": "Number"}}
'
