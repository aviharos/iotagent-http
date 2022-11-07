curl --location --request POST 'localhost:4315' \
--header 'Content-Type: text/plain' \
--data-raw '{
                "url": "http://orion:1026/v2/entities/urn:ngsi_ld:Storage:1/attrs/Failed/value",
                "method": "PUT",
                "headers": [
                    "Content-Type: text/plain"
                ],
                "data": true
            }'
