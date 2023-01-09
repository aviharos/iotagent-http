"""The main part of the plugin that transforms the HTTP request 

The transform function will be applied to the HTTPRequest object before sending it. 
"""
# Standard Library imports
import os
import sys

# PyPI imports

# custom imports
from . import Orion
from . import Logger

logger = Logger.getLogger(__name__)

sys.path.insert(0, "..")
from HTTPRequest import HTTPRequest

ORION_HOST = os.environ.get("ORION_HOST")
ORION_PORT = os.environ.get("ORION_PORT")


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
            "url": "",
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
    Find the Workstation's Job. Find the Job's part. Find the partsPerCycle.
    Multiply the counter by the partsPerCycle value
    to get the actual value of the Job's counter.
    Set the counter accordingly: the GoodPartCounter
    if "ct" contains "good", the RejectPartCounter otherwise.

   For example if the current Job is Job:202200045,
   the HTTPRequest will be transformed to the equivalent of

   curl --location --request PUT 'http://orion:1026/v2/entities/urn:ngsi_ld:Job:202200045/attrs/GoodPartCounter/value' \
--header 'Content-Type: text/plain' \
--data-raw '96'

    partsPerCycle: 8
    So the GoodPartCounter's real value must be 8*14 = 96

    The plugin needs setting the ORION_HOST and ORION_PORT
    environment variables.

    Steps:
        1. Check if the transform attribute of the HTTPRequest is empy or not
            If empty, the transform function returns the request unchanged
        2. If the transform attribute of the HTTPRequest does not contain a valid Orion id,
            the transform function returns the request unchanged
        3. Get the Workstation Orion object whose id is in the transform attribute
        4. Get the refJob attribute
        5. Get the Job from Orion
        6. Get the Job's refPart
        7. Get the Part from Orion
        8. Get the Operation based on the CurrentOperationType of the Job
        9. Get partsPerCycle
        10. Multiply "cc" (cycle count) by partsPerCycle to get the Counter
        11. Check if the GoodPartCounter or the RejectPartCounter
            needs to be updated (transform["ct"])
        12. Construct a HTTPRequest that updates the Job's counter.
        13. Return request
        """
    if req.transform == {}:
        # do not modify a request without an empty transform field
        return req
    ws_id = req.transform["ws"]
    logger.debug(f"wd_id: {ws_id}")
    counter_type = req.transform["ct"]
    logger.debug(f"counter_type: {counter_type}")
    if counter_type == "good":
        counter_name = "goodPartCounter"
    else:
        counter_name = "rejectPartCounter"
    logger.debug(f"counter_name: {counter_name}")
    cycle_count = req.transform["cc"]
    logger.debug(f"cycle_count: {cycle_count}")
    if not Orion.exists(ws_id):
        logger.error(f"Error: cannot transform request: Workstation {ws_id} does not exist")
        return req
    workstation = Orion.get(ws_id)
    logger.debug(f"workstation: {workstation}")
    job_id = workstation["refJob"]["value"]
    job = Orion.get(job_id)
    logger.debug(f"job: {job}")
    # part_id = job["refPart"]["value"]
    operation_id = job["refOperation"]["value"]
    operation = Orion.get(operation_id)
    logger.debug(f"operation: {operation}")
    partsPerCycle = operation["partsPerCycle"]["value"]
    logger.debug(f"partsPerCycle: {partsPerCycle}")
    counter_value = cycle_count * partsPerCycle
    logger.debug(f"counter_value: {counter_value}")
    url = f"http://{ORION_HOST}:{ORION_PORT}/v2/entities/{job_id}/attrs/{counter_name}/value"
    logger.debug(f"url: {url}")
    method = "PUT"
    headers = {"Content-Type": "text/plain"}
    data = str(counter_value)
    logger.debug(f"data: {data}")
    transformed = HTTPRequest(url=url, method=method, headers=headers, data=data)
    logger.debug(f"transformed request: {transformed}")
    return transformed
