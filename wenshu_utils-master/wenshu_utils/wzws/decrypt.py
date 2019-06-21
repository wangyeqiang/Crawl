# coding: utf-8
import base64
import re
from urllib import parse

import execjs
from execjs.runtime_names import Node
from lxml.etree import HTML


def wzws_decrypt(text: str, url: str = None) -> str:
    """
    :param text: 提示"请开启JavaScript并刷新该页"的响应text
    :param url: 当前请求的url，如果提供url将使用Python实现的算法计算结果，速度很多
                如果不传url，将调用外部的nodejs解析得到结果，会慢一些
                url示例: http://wenshu.court.gov.cn/CreateContentJS/CreateContentJS.aspx?DocID=13d4c01a-0734-4ec1-bbac-658f8bb8ec62

    :return: 重定向url，访问重定向url后会返回wzws_cid的cookie和正确的响应
    """
    if url is None:
        base_url = "http://wenshu.court.gov.cn"
        custom_js = """
        window = {};
        document = {
            createElement: () => ({ style: "", appendChild: () => ({}), submit: () => ({}) }),
            body: { appendChild: obj => { window.location = obj.action } }
        };
        atob = str => Buffer.from(str, "base64").toString("binary");
        get_location = () => window.location;
        """
        html = HTML(text)
        js = html.xpath("//script/text()")[0]

        ctx = execjs.get(Node).compile(custom_js + js)
        location = ctx.call("get_location")

        redirect_url = parse.urljoin(base_url, location)

    else:
        prefix_url = "http://wenshu.court.gov.cn/WZWSRE"

        parse_result = parse.urlparse(url)
        request_path = (parse_result.path + "?" + parse_result.query) if parse_result.query else parse_result.path
        encoded_path = base64.b64encode(request_path.encode()).decode()

        question, factor = re.search(r'wzwsquestion="(.+?)".+wzwsfactor="(\d+)"', text).groups()

        challenge = "WZWS_CONFIRM_PREFIX_LABEL{}".format(sum(ord(i) for i in question) * int(factor) + 111111)
        query_params = "wzwschallenge={}".format(base64.b64encode(challenge.encode()).decode())

        redirect_url = prefix_url + encoded_path + "?" + query_params

    return redirect_url
