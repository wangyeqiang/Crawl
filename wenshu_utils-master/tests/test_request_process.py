# coding: utf-8
"""
测试从列表页到详情页的请求过程
测试包含:
1. vl5x的生成(vjkl5可以自生成, 服务器不会校验vjkl5, 只需让vjkl5和vl5x相互配对即可)
2. RunEval的解密
3. DocID的解密
4. wzws的解密
5. 数据的解析
"""
import json
import unittest
from pprint import pprint

import requests

from wenshu_utils.docid.decrypt import decrypt_doc_id
from wenshu_utils.docid.runeval import parse_run_eval
from wenshu_utils.document.parse import parse_detail
from wenshu_utils.vl5x.args import Vjkl5, Vl5x, Number, Guid
from wenshu_utils.wzws.decrypt import wzws_decrypt


class TestRequestProcess(unittest.TestCase):
    def setUp(self):
        self.error_msg = "请开启JavaScript并刷新该页"

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
        })

    def tearDown(self):
        self.session.close()

    def test_request_process(self):
        vjkl5 = Vjkl5()
        self.session.cookies["vjkl5"] = vjkl5

        url = "http://wenshu.court.gov.cn/List/ListContent"
        data = {
            "Param": "关键词:合同",
            "Index": 1,
            "Page": 10,
            "Order": "法院层级",
            "Direction": "asc",
            "vl5x": Vl5x(vjkl5),
            "number": Number(),
            "guid": Guid(),
        }
        response = self.session.post(url, data=data)

        json_data = json.loads(response.json())
        print("列表数据:", json_data)

        run_eval = json_data.pop(0)["RunEval"]
        try:
            key = parse_run_eval(run_eval)
        except ValueError as e:
            raise ValueError("返回脏数据") from e
        else:
            print("RunEval解析完成:", key, "\n")

        key = key.encode()
        for item in json_data:
            cipher_text = item["文书ID"]
            print("解密:", cipher_text)
            plain_text = decrypt_doc_id(doc_id=cipher_text, key=key)
            print("成功, 文书ID:", plain_text, "\n")

        # 请求详情页
        detail_url = "http://wenshu.court.gov.cn/CreateContentJS/CreateContentJS.aspx"
        params = {
            "DocID": decrypt_doc_id(doc_id=json_data[0]["文书ID"], key=key),
        }
        response = self.session.get(detail_url, params=params)
        text = response.content.decode()

        if self.error_msg in text:
            redirect_url1 = wzws_decrypt(text, url=response.url)
            redirect_url2 = wzws_decrypt(text)
            self.assertEqual(redirect_url1, redirect_url2)

            response = self.session.get(redirect_url1)

        self.assertNotIn(self.error_msg, response.content.decode())

        group_dict = parse_detail(response.text)
        pprint(group_dict)


if __name__ == '__main__':
    unittest.main()
