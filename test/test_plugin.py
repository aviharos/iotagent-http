"""A file for testing transform.py, the core of the plugin

This file modifies Orion data 
and also needs setting a few environment variables
Never run it in a production environment!
"""

# Standard Library imports
import os
import sys
import unittest

# Custom imports
sys.path.insert(0, "../app")
from HTTPRequest import HTTPRequest
from plugin import transform, Orion

ORION_HOST = os.environ.get("ORION_HOST")
ORION_PORT = os.environ.get("ORION_PORT")


class TestIotAgent(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ws = {
            "type": "Workstation",
            "id": "urn:ngsi_ld:Workstation:1",
            "Available": {"type": "Boolean", "value": True},
            "Alert": {"type": "Text", "value": None},
            "RefJob": {"type": "Relationship", "value": "urn:ngsi_ld:Job:202200045"},
            "RefOEE": {"type": "Relationship", "value": "urn:ngsi_ld:OEE:1"},
            "RefThroughput": {
                "type": "Relationship",
                "value": "urn:ngsi_ld:Throughput:1",
            },
            "RefOperatorSchedule": {
                "type": "Relationship",
                "value": "urn:ngsi_ld:OperatorSchedule:1",
            },
        }
        cls.job = {
            "type": "Job",
            "id": "urn:ngsi_ld:Job:202200045",
            "RefPart": {"type": "Relationship", "value": "urn:ngsi_ld:Part:Core001"},
            "RefWorkstation": {
                "type": "Relationship",
                "value": "urn:ngsi_ld:Workstation:1",
            },
            "JobNumber": {"type": "Number", "value": 202200045},
            "CurrentOperationType": {
                "type": "Text",
                "value": "Core001_injection_moulding",
            },
            "JobTargetNumber": {"type": "Number", "value": 8000},
            "JobStartDate": {"type": "Date", "value": "2022-03-21"},
            "JobEndDate": {"type": "Date", "value": "2022-03-24"},
            "JobDueDate": {"type": "Date", "value": "2022-03-31"},
            "GoodPartCounter": {"type": "Number", "value": 0},
            "RejectPartCounter": {"type": "Number", "value": 0},
            "Finished": {"type": "Boolean", "value": False},
        }
        cls.part = {
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
                            "value": "Core001_injection_moulding",
                        },
                        "CycleTime": {"type": "Number", "value": 46},
                        "PartsPerCycle": {"type": "Number", "value": 8},
                    }
                ],
            },
        }
        Orion.update([cls.ws, cls.job, cls.part])

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_transform(self):
        # Good parts completed
        req_good = HTTPRequest(
            headers={},
            url=f"http://{ORION_HOST}:{ORION_PORT}/v2/entities",
            method="PUT",
            transform={"ws": "urn:ngsi_ld:Workstation:1", "ct": "good", "cc": 14},
        )
        req_good_expected = HTTPRequest(url=f"http://{ORION_HOST}:{ORION_PORT}/v2/entities/{self.job['id']}/attrs/GoodPartCounter/value",
                headers={"Content-Type": "text/plain"},
                method="PUT",
                data=str(req_good.transform["cc"] * self.part["Operations"]["value"][0]["PartsPerCycle"]["value"])
                )
        req_good_transformed = transform(req_good)
        self.assertEqual(req_good_expected, req_good_transformed)

        # Reject parts completed
        req_reject = HTTPRequest(
            headers={},
            url=f"http://{ORION_HOST}:{ORION_PORT}/v2/entities",
            method="PUT",
            transform={"ws": "urn:ngsi_ld:Workstation:1", "ct": "reject", "cc": 14},
        )
        req_reject_expected = HTTPRequest(url=f"http://{ORION_HOST}:{ORION_PORT}/v2/entities/{self.job['id']}/attrs/RejectPartCounter/value",
                headers={"Content-Type": "text/plain"},
                method="PUT",
                data=str(req_reject.transform["cc"] * self.part["Operations"]["value"][0]["PartsPerCycle"]["value"])
                )
        req_reject_transformed = transform(req_reject)
        self.assertEqual(req_reject_expected, req_reject_transformed)

if __name__ == "__main__":
    unittest.main()
