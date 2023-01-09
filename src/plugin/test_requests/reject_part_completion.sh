curl --location --request POST 'http://localhost:4315' \
--header 'Content-Type: application/json' \
--data-raw '{
    "url": "",
    "method": "PUT",
    "headers": ["Content-Type: application/json"],
    "data": {},
    "transform": {
        "ws": "urn:ngsiv2:i40Asset:Workstation1",
        "ct": "reject",
        "cc": 11
    }
}'
