curl --location --request POST 'localhost:4315' \
--header 'Content-Type: text/plain' \
--data-raw '{"url": "http://orion:1026/v2/entities",
"method": "POST",
"headers": ["Content-Type: application/json"],
"data": {
"type": "Storage",
"id": "urn:ngsi_ld:Storage:1",
"Capacity": {"type": "Number", "value": 100},
"Counter": {"type": "Number", "value": 100},
"Failed": {"type": "Boolean", "value": false}
}}
'
