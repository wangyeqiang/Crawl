# coding: utf-8
"""
测试包含:
1. 详情页数据解析的正则
"""
import unittest
from pprint import pprint

import requests

from wenshu_utils.document.parse import parse_detail
from wenshu_utils.wzws.decrypt import wzws_decrypt


class TestDetailParse(unittest.TestCase):
    def setUp(self):
        self.error_msg = "请开启JavaScript并刷新该页"

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36",
        })

    def tearDown(self):
        self.session.close()

    def test_detail_parse(self):
        url = "http://wenshu.court.gov.cn/CreateContentJS/CreateContentJS.aspx"
        params = {
            "DocID": "2e509686-62f9-4cf8-beeb-a7fe00ebcb05",
        }
        response = self.session.get(url, params=params)
        text = response.content.decode()

        if self.error_msg in text:
            redirect_url = wzws_decrypt(text)
            response = self.session.get(redirect_url)

        self.assertNotIn(self.error_msg, response.content.decode())

        group_dict = parse_detail(response.text)
        pprint(group_dict)


if __name__ == '__main__':
    unittest.main()
