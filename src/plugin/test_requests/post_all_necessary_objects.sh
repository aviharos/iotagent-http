curl --location --request POST 'http://localhost:1026/v2/op/update' \
--header 'Content-Type: application/json' \
--data-raw '{
    "actionType": "append",
    "entities": [
        {
            "id": "urn:ngsiv2:i40Asset:Workstation1",
            "type": "i40Asset",
            "i40AssetType": {
                "type": "Text",
                "value": "Workstation"
            },
            "available": {
                "type": "Boolean",
                "value": true
            },
            "refJob": {
                "type": "Relationship",
                "value": "urn:ngsiv2:i40Process:Job202200045"
            },
            "refShift": {
                "type": "Relationship",
                "value": "urn:ngsiv2:i40Recipe:Shift1"
            },
            "oee": {
                "type": "Number",
                "value": null
            },
            "oeeAvailability": {
                "type": "Number",
                "value": null
            },
            "oeePerformance": {
                "type": "Number",
                "value": null
            },
            "oeeQuality": {
                "type": "Number",
                "value": null
            },
            "oeeObject": {
                "type": "OEE",
                "value": {
                    "oee": null,
                    "availability": null,
                    "performance": null,
                    "quality": null 
                }
            },
            "throughputPerShift": {
                "type": "Number",
                "value": null
            }
        },
        {
            "id": "urn:ngsiv2:i40Process:Job202200045",
            "type": "i40Process",
            "i40ProcessType": {"type": "Text", "value": "Job"},
            "refPart": {
                "type": "Relationship",
                "value": "urn:ngsiv2:i40Asset:Part_Core001"
            },
            "refOperation": {
                "type": "Relationship",
                "value": "urn:ngsiv2:i40Recipe:Operation_Core001_injectionMoulding"
            },
            "jobTargetNumber": {
                "type": "Number",
                "value": 8000
            },
            "goodPartCounter": {
                "type": "Number",
                "value": 0
            },
            "rejectPartCounter": {
                "type": "Number",
                "value": 0
            }
        },
        {
            "id": "urn:ngsiv2:i40Recipe:Operation_Core001_injectionMoulding",
            "type": "i40Recipe",
            "i40RecipeType": {"type": "Text", "value": "Operation"},
            "refSequenceOfOperations": {
                "type": "Relationship",
                "value": "urn:ngsiv2:i40Recipe:SequenceOfOperations_Core001"
            },
            "cycleTime": {
                "type": "Number",
                "value": 46
            },
            "partsPerCycle": {
                "type": "Number",
                "value": 8
            }
        }
    ]
}
'
