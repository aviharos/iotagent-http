# -*- coding: utf-8 -*-
# Standard Library imports
'''
The agent needs to run for some tests
python main.py
'''

import copy
import os
import unittest
import sys

sys.path.insert(0, '../app')
from main import IoTAgent
from HTTPRequest import HTTPRequest
from Logger import getLogger

ORION_HOST = os.environ.get("ORION_HOST")
ORION_PORT = os.environ.get("ORION_PORT")
PORT = os.environ.get("PORT")


class TestIotAgent(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.logger = getLogger(__name__)
    
    @classmethod
    def tearDownClass(cls):
        pass
    
    def setUp(self):
        # TODO add transform
        self.pd_post = {"url": f"http://{ORION_HOST}:{ORION_PORT}/v2/entities",
                        "method": "POST",
                        "headers": ["Content-Type: application/json"],
                        "data": {
                        "type": "Storage",
                        "id": "urn:ngsi_ld:Storage:1",
                        "Capacity": {"type": "Number", "value": 100},
                        "Counter": {"type": "Number", "value": 100}
                        }}
        self.pd_get = {"url": f"http://{ORION_HOST}:{ORION_PORT}/v2/entities/urn:ngsi_ld:Storage:1",
                       "method": "GET",
                       "headers": []
                       }
        self.pd_put = {"url": f"http://{ORION_HOST}:{ORION_PORT}/v2/entities/urn:ngsi_ld:Storage:1/attrs/Counter",
                       "method": "PUT",
                       "headers": ["Content-Type: application/json"],
                       "data": {"value": {"$inc": -1}, "type": "Number"}}
        self.pd_delete = {"url": f"http://{ORION_HOST}:{ORION_PORT}/v2/entities/urn:ngsi_ld:Storage:1",
                          "method": "DELETE",
                          "headers": []
                          }
        self.pd_transform = {"url": f"http://{ORION_HOST}:{ORION_PORT}/v2/entities",
                        "method": "POST",
                        "headers": ["Content-Type: application/json"],
                        "transform": {"cc": 10,
                            "ct": "good"},
                        "data": {
                        "type": "Storage",
                        "id": "urn:ngsi_ld:Storage:1",
                        "Capacity": {"type": "Number", "value": 100},
                        "Counter": {"type": "Number", "value": 100}
                        }}
        self.headers = {"Content-Type": "application/json"}
        self.req_post = HTTPRequest(url=self.pd_post['url'],
                               headers={"Content-Type": "application/json", 'Content-Length': str(len(str(self.pd_post['data'])))},
                               transform={},
                               method=self.pd_post['method'],
                               data=str(self.pd_post['data']).replace('\'', '"'))
        self.req_put = HTTPRequest(url=self.pd_put['url'],
                              headers={"Content-Type": "application/json", 'Content-Length': str(len(str(self.pd_put['data'])))},
                              transform={},
                              method=self.pd_put['method'],
                              data=str(self.pd_put['data']).replace('\'', '"'))
        self.req_get = HTTPRequest(url=self.pd_get['url'],
                              headers={},
                              transform={},
                              method=self.pd_get['method'])
        self.req_delete = HTTPRequest(url=self.pd_delete['url'],
                                 headers={},
                                 transform={},
                                 method=self.pd_delete['method'])
        self.req_transform = HTTPRequest(url=self.pd_post['url'],
                               headers={"Content-Type": "application/json", 'Content-Length': str(len(str(self.pd_post['data'])))},
                               transform=self.pd_transform["transform"],
                               method=self.pd_post['method'],
                               data=str(self.pd_post['data']).replace('\'', '"'))
    
    def tearDown(self):
        pass

    # def test_load_plugin_transform_use_plugin_false(self):
    #     transform = load_plugin_transform(False)
    #     self.assertEqual(transform, None)

    def test_load_plugin_transform_use_plugin_true(self):
        main_loaded_transform = load_plugin_transform(True)
        self.assertEqual(main_loaded_transform, imported_transform)
        main_loaded_transform = load_plugin_transform(False)
        self.assertEqual(main_loaded_transform, None)

    def test__clean_keys(self):
        self.pd_post_k = self.pd_post.copy()
        self.pd_post_k[' MethoD '] = self.pd_post['method']
        del(self.pd_post_k['method'])
        self.pd_post_k['uRL '] = self.pd_post['url']
        del(self.pd_post_k['url'])
        self.pd_post_k[' DATA'] = self.pd_post['data']
        del(self.pd_post_k['data'])
        self.pd_post_k = IoTAgent._clean_keys(IoTAgent, self.pd_post_k)
        self.assertEqual(self.pd_post, self.pd_post_k)

    def test__validate_method(self):
        self.assertIsNone(IoTAgent._validate_method(IoTAgent, self.pd_post))
        self.pd_post['method'] = 'HEAD'
        with self.assertRaises(NotImplementedError):
            IoTAgent._validate_method(IoTAgent, self.pd_post)
        self.pd_post['method'] = 'CONNECT'
        with self.assertRaises(NotImplementedError):
            IoTAgent._validate_method(IoTAgent, self.pd_post)
        self.pd_post['method'] = 'OPTIONS'
        with self.assertRaises(NotImplementedError):
            IoTAgent._validate_method(IoTAgent, self.pd_post)
        self.pd_post['method'] = 'TRACE'
        with self.assertRaises(NotImplementedError):
            IoTAgent._validate_method(IoTAgent, self.pd_post)
        self.pd_post['method'] = 'ELSE'
        with self.assertRaises(ValueError):
            IoTAgent._validate_method(IoTAgent, self.pd_post)

    def test__validate_mandatory_keys(self):
        del(self.pd_post['url'])
        with self.assertRaises(KeyError):
            IoTAgent._validate_mandatory_keys(IoTAgent, self.pd_post)
        del(self.pd_put['data'])
        with self.assertRaises(KeyError):
            IoTAgent._validate_mandatory_keys(IoTAgent, self.pd_put)
        del(self.pd_get['method'])
        with self.assertRaises(KeyError):
            IoTAgent._validate_mandatory_keys(IoTAgent, self.pd_get)
        del(self.pd_delete['headers'])
        with self.assertRaises(KeyError):
            IoTAgent._validate_mandatory_keys(IoTAgent, self.pd_delete)
    
    def test__validate_headers(self):
        self.pd_post['headers'][0] = "  Content-Type  : application/json  "
        self.assertIsNone(IoTAgent._validate_headers(IoTAgent, self.pd_post))
        self.pd_post['headers'][0] = "  Content-Length  "
        self.assertIsNone(IoTAgent._validate_headers(IoTAgent, self.pd_post))
        self.pd_post['headers'].append("  Content-Type  : application/json : true  ")
        with self.assertRaises(ValueError):
            IoTAgent._validate_headers(IoTAgent, self.pd_post)

    def test__extract_headers(self):
        self.assertEqual(IoTAgent._extract_headers(IoTAgent, self.pd_post), {"Content-Type": "application/json"})
        self.pd_post['headers'].append('Some header without content')
        self.assertEqual(IoTAgent._extract_headers(IoTAgent, self.pd_post), {"Content-Type": "application/json", 'Some header without content': None})

    def test__validate_url(self):
        self.assertIsNone(IoTAgent._validate_url(IoTAgent, self.pd_post))

    def tets__validate_content(self):
        headers = {"Content-Type": "application/json"}
        self.assertIsNone(IoTAgent._validate_content(IoTAgent, self.pd_post, headers))
        self.assertIsNone(IoTAgent._validate_content(IoTAgent, self.pd_put, headers))
        with self.assertRaises(ValueError):
            IoTAgent._validate_content(IoTAgent, self.pd_post, {"Content": "application/json"})
        with self.assertRaises(ValueError):
            IoTAgent._validate_content(IoTAgent, self.pd_post, {"Content-Type": "application/text"})
        self.pd_post['data'] = 'test'
        with self.assertRaises(ValueError):
            IoTAgent._validate_content(IoTAgent, self.pd_post, headers)
        self.pd_post['data'] = ''
        with self.assertRaises(ValueError):
            IoTAgent._validate_content(IoTAgent, self.pd_post, headers)

    def test__construct_request(self):
        self.assertEqual(IoTAgent._construct_request(IoTAgent, self.pd_post, self.headers), self.req_post)
        self.assertEqual(IoTAgent._construct_request(IoTAgent, self.pd_put, self.headers), self.req_put)
        self.assertEqual(IoTAgent._construct_request(IoTAgent, self.pd_get, {}), self.req_get)
        self.assertEqual(IoTAgent._construct_request(IoTAgent, self.pd_delete, {}), self.req_delete)
        self.assertEqual(IoTAgent._construct_request(IoTAgent, self.pd_transform, self.headers), self.req_transform)

    def test__send_request_to_broker(self):
        res = IoTAgent._send_request_to_broker(IoTAgent, self.req_post)
        self.assertEqual(res.status_code, 201)
        res = IoTAgent._send_request_to_broker(IoTAgent, self.req_put)
        self.assertEqual(res.status_code, 204)
        res = IoTAgent._send_request_to_broker(IoTAgent, self.req_get)
        self.assertEqual(res.status_code, 200)
        res = IoTAgent._send_request_to_broker(IoTAgent, self.req_delete)
        self.assertEqual(res.status_code, 204)

    # def test__apply_plugin_if_present(self):
    #     """Test if the plugin is applied well. 
    #
    #     We test that transform == None should not change the request.
    #
    #     As for transform != None:
    #     This function creates a copy of the IoTAgent class definition, 
    #     monkey patches the transform module with a custom one 
    #     that replaces "cc" with 11 in transform.
    #
    #     Then the apply_plugi_if_present function is called and we can test 
    #     if the patched transform method was properly called.
    #     """
    #     IoTAgent_mod = copy.deepcopy(IoTAgent)
    #     IoTAgent_mod.transform = None
    #     transformed = IoTAgent_mod._apply_plugin_if_present(IoTAgent_mod, self.req_transform)
    #     self.assertEqual(transformed, self.req_transform)

        # def test_transform(req: HTTPRequest):
        #     new_transform = req.transform
        #     new_transform["cc"] = 11
        #     return HTTPRequest(url = req.url,
        #             headers = req.headers,
        #             transform = new_transform,
        #             method = req.method,
        #             data = req.data)
        # IoTAgent_mod = copy.deepcopy(IoTAgent)
        # IoTAgent_mod.transform = test_transform
        # transformed = IoTAgent_mod._apply_plugin_if_present(IoTAgent_mod, self.req_transform)
        # self.assertEqual(transformed, test_transform(self.req_transform))
        # self.assertEqual(transformed.transform["cc"], 11)


if __name__ == '__main__':
    unittest.main()
