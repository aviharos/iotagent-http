curl --location --request POST 'http://localhost:4315' \
--header 'Content-Type: application/json' \
--data-raw '{
    "url": "",
    "method": "PUT",
    "headers": ["Content-Type: application/json"],
    "data": {},
    "transform": {
        "ws": "urn:ngsi_ld:Workstation:1",
        "ct": "reject",
        "cc": 11
    }
}'
