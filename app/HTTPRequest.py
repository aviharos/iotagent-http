# -*- coding: utf-8 -*-
# Standard Library imports
from dataclasses import dataclass, field


@dataclass
class HTTPRequest:
    url: str
    headers: dict
    transform: dict
    method: str = field(default='GET')
    data: str = field(default='')
