"""The main part of the plugin that transforms the HTTP request 

The transform function will be applied to the HTTPRequest object before sending it. 
"""
# Standard Library imports
import sys
from urllib.parse import urlparse

# PyPI imports

# custom imports
import Orion

sys.path.insert(0, "..")
from HTTPRequest import HTTPRequest


def transform(req: HTTPRequest):
    """Transform a HTTPRequest object

    Args:
        req (HTTPRequest): request to transform

    Returns:
        a transformed HTTPRequest object

    In this Robo4Toys TTE's use case, the transform function will help
    updating the counters of the Jobs.
    The problem is that the PLC does not know the current Job to set,
    so it cannot provide all necessary information
    The PLC will send data packets as follows:

        {
            "url": "http://orion:1026/v2/entities",
            "method": "PUT",
            "headers": [],
            "data": null,
            "transform": {
                "ws": "urn:ngsi_ld:Workstation:1",
                "ct": "good", # counter type
                "cc": 14, # cycle count
            }
        }

    This means that the urn:ngsi_ld:Workstation:1
    signals that good parts were created,
    the number of successful cycles so far is 14.
    The transform module needs to transform this as follows.
    Find the Workstation's Job. Find the Job's part. Find the PartsPerCycle.
    Multiply the counter by the PartsPerCycle value
    to get the actual value of the Job's counter.
    Set the counter accordingly: the GoodPartCounter
    if "ct" contains "good", the RejectPartCounter otherwise.

   For example if the current Job is Job:202200045,
   the HTTPRequest will be transformed to the equivalent of

   curl --location --request PUT 'http://orion:1026/v2/entities/urn:ngsi_ld:Job:202200045/attrs/GoodPartCounter/value' \
--header 'Content-Type: text/plain' \
--data-raw '96'

    PartsPerCycle: 8
    So the GoodPartCounter's real value must be 8*14 = 96

    Steps:
        1. Check if the transform attribute of the HTTPRequest is empy or not
            If empty, the transform function returns the request unchanged
        2. If the transform attribute of the HTTPRequest does not contain a valid Orion id,
            the transform function returns the request unchanged
        3. Get the Workstation Orion object whose id is in the transform attribute
        4. Get the RefJob attribute
        5. Get the Job from Orion
        6. Get the Job's RefPart
        7. Get the Part from Orion
        8. Get the Operation based on the CurrentOperationType of the Job
        9. Get PartsPerCycle
        10. Multiply "cc" (cycle count) by PartsPerCycle to get the Counter
        11. Check if the GoodPartCounter or the RejectPartCounter
            needs to be updated (transform["ct"])
        12. Construct a HTTPRequest that updates the Job's counter.
        13. Return request
        """
    if req.transform == {}:
        return req
    ws_id = req.transform["ws"]
    counter_type = req.transform["ct"]
    if counter_type == "good":
        counter_name = "GoodPartCounter"
    else:
        counter_name = "RejectPartCounter"
    cycle_count = req.transform["cc"]
    if not Orion.exists(ws_id):
        return req
    workstation = Orion.get(ws_id)
    job_id = workstation["RefJob"]["value"]
    job = Orion.get(job_id)
    part_id = job["RefPart"]["value"]
    current_operation_type = job["CurrentOperationType"]["value"]
    part = Orion.get(part_id)
    operation = None
    for op in part["Operations"]["value"]:
        if op["OperationType"] == current_operation_type:
            operation = op
            break
    if operation is None:
        raise ValueError(
            f"The job's current operation is not found in the referred part.\n{job}\n{part}"
        )
    partsPerCycle = operation["PartsPerCycle"]
    counter_value = cycle_count * partsPerCycle
    parsed = urlparse(req.url)
    orion_host = parsed.hostname
    orion_port = parsed.port
    url = f"http://{orion_host}:{orion_port}/v2/entities/{job_id}/attrs/{counter_name}/value"
    method = "PUT"
    headers = ["Content-Type: text/plain"]
    data = str(counter_value)
    transformed = HTTPRequest(url=url, method=method, headers=headers, data=data)
    return transformed
