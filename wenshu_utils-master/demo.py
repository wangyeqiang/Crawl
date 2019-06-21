# coding: utf-8
import json
from pprint import pprint

import requests

from wenshu_utils.docid.decrypt import decrypt_doc_id
from wenshu_utils.docid.runeval import parse_run_eval
from wenshu_utils.document.parse import parse_detail
from wenshu_utils.vl5x.args import Vjkl5, Vl5x, Number, Guid
from wenshu_utils.wzws.decrypt import wzws_decrypt


def request_list():
    """请求列表数据"""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
    })

    vjkl5 = Vjkl5()
    session.cookies["vjkl5"] = vjkl5

    list_url = "http://wenshu.court.gov.cn/List/ListContent"
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
    response = session.post(list_url, data=data)

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


def request_detail():
    """请求详情数据"""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36",
    })

    url = "http://wenshu.court.gov.cn/CreateContentJS/CreateContentJS.aspx"
    params = {
        "DocID": "13d4c01a-0734-4ec1-bbac-658f8bb8ec62",
    }
    response = session.get(url, params=params)
    text = response.content.decode()

    if "请开启JavaScript并刷新该页" in text:
        # 如果有当前请求的url，尽量把url传进去，会更快一些
        redirect_url = wzws_decrypt(text, url=response.url)
        # 没有url就算了
        # redirect_url = wzws_decrypt(text)

        response = session.get(redirect_url)

    group_dict = parse_detail(response.text)
    pprint(group_dict)


if __name__ == '__main__':
    request_list()
    request_detail()
