curl --location --request POST 'http://localhost:1026/v2/op/update' \
--header 'Content-Type: application/json' \
--data-raw '{
    "actionType": "append",
    "entities": [
        {
            "type": "Workstation",
            "id": "urn:ngsi_ld:Workstation:1",
            "Available": {"type": "Boolean", "value": true},
            "Alert": {"type": "Text", "value": null},
            "RefJob": {"type": "Relationship", "value": "urn:ngsi_ld:Job:202200045"},
            "RefOEE": {"type": "Relationship", "value": "urn:ngsi_ld:OEE:1"},
            "RefThroughput": {
                "type": "Relationship",
                "value": "urn:ngsi_ld:Throughput:1"
            },
            "RefOperatorSchedule": {
                "type": "Relationship",
                "value": "urn:ngsi_ld:OperatorSchedule:1"
            }
        },
        {
            "type": "Job",
            "id": "urn:ngsi_ld:Job:202200045",
            "RefPart": {"type": "Relationship", "value": "urn:ngsi_ld:Part:Core001"},
            "RefWorkstation": {
                "type": "Relationship",
                "value": "urn:ngsi_ld:Workstation:1"
            },
            "JobNumber": {"type": "Number", "value": 202200045},
            "CurrentOperationType": {
                "type": "Text",
                "value": "Core001_injection_moulding"
            },
            "JobTargetNumber": {"type": "Number", "value": 8000},
            "JobStartDate": {"type": "Date", "value": "2022-03-21"},
            "JobEndDate": {"type": "Date", "value": "2022-03-24"},
            "JobDueDate": {"type": "Date", "value": "2022-03-31"},
            "GoodPartCounter": {"type": "Number", "value": 0},
            "RejectPartCounter": {"type": "Number", "value": 0},
            "Finished": {"type": "Boolean", "value": false}
        },
        {
            "type": "Part",
            "id": "urn:ngsi_ld:Part:Core001",
            "Operations": {
                "type": "List",
                "value": [
                    {
                        "type": "Operation",
                        "OperationNumber": {"type": "Number", "value": 10},
                        "OperationType": {
                            "type": "Text",
                            "value": "Core001_injection_moulding"
                        },
                        "CycleTime": {"type": "Number", "value": 46},
                        "PartsPerCycle": {"type": "Number", "value": 8}
                    }
                ]
            }
        }
    ]
}
'
