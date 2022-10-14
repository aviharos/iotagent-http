# -*- coding: utf-8 -*-
"""The HTTPRequest class 
"""

# Standard Library imports
from dataclasses import dataclass, field


@dataclass
class HTTPRequest:
    """ A simple HTTPRequest dataclass
    
    If a plugin is used, the plugin.transform
    takes an HTTPRequest and transforms it to another HTTPRequest

    The vanilla IoTAgent does not contain a plugin
    and thus does not uses the transform field.
    The transform field may be used to pass moTe information
    to the plugin.transform module
    """
    url: str
    headers: dict
    method: str
    transform: dict = field(default_factory=lambda: {})
    data: str = field(default='')
