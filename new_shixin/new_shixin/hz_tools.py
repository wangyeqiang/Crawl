#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author: wangyq
@version: 1.0
@file: hz_webdriver_middleware.py
@time: 2018/12/6 下午11:31
@desc:
"""
import math
import json
import datetime
from collections import defaultdict
import re
# from .settings import WEB_USER_AGENT
import requests
from scrapy import Selector
from scrapy.http import HtmlResponse
import random
import time
from io import BytesIO

try:
    import cPickle as pickle
except ImportError as e:
    import pickle


# 以下为获取插件方法
def is_attachment_link(url):
    """
    # 判断是否为附件连接
    :param url:
    :return:
    """
    return ('.pdf' in url) or ('.doc' in url) or ('.docx' in url) or ('.xls' in url) or ('.xlsx' in url) or (
            '.rar' in url) or ('.zip' in url)


def is_img_link(url):
    """
    # 判断图片连接
    :param url:
    :return:
    """
    return (url.endswith('jpg')) or (url.endswith('jpeg')) or (url.endswith('png'))(url.endswith('bmp'))


def get_attachments(response, a_selector):
    """
    获取附件URL
    :param a_selector:
    :param response
    :return: attachments
    """
    attachments = list()
    for a in a_selector:
        url = a.xpath('./@href').extract_first()
        name = ''.join(a.xpath('.//text()').extract()).strip()
        if url and (is_attachment_link(url) or is_attachment_link(name)):
            url = response.urljoin(url.strip())
            attachments.append({"url": url, "name": name})
    return attachments


def get_img(response, img_selector):
    """
    获取图片附件
    :param response:
    :param img_selector:
    :return:
    """
    img_list = list()
    for a in img_selector:
        url = a.xpath('./@src').extract_first()
        if url:
            url = response.urljoin(url.strip())
            name = url if is_img_link(url) else url + '.jpg'  # 如果是img格式连接则以url命名，否则在为url + .jpg
            img_list.append({"url": url, "name": name})
    return img_list


# 以下为获取时间判断日增方法
def get_today():
    """
    # 获取今日data %Y-%m-%d 2018-12-07
    """
    today = datetime.date.today()  # - datetime.timedelta(days=1)
    ISOFOMAT = "%Y-%m-%d"
    return today.strftime(ISOFOMAT)  # 为str


def get_yesterday(days=1):
    """
    # 用于月增，季度增等，和之前某一天时间判断
    """
    today = datetime.date.today()
    oneday = datetime.timedelta(days=days)
    yesterday = (today - oneday).strftime('%Y-%m-%d')
    return yesterday


def get_today_date():
    """
    # 获取今日data "%Y年%m月%d日" 2018年12月7日
    """
    today = datetime.date.today()
    ISOFOMAT = "%Y年%m月%d日"
    return today.strftime(ISOFOMAT)


def get_today_time():
    """
    # 获取今日data "%Y%m%d"   20181207
    """
    today = datetime.date.today()
    ISOFOMAT = "%Y%m%d"
    return today.strftime(ISOFOMAT)


def cmp_date(date1, date2):
    """
    解决判断日更日期显示2018-11-1问题（正常为2018-11-01）
    :param date1:  时间str  date1可为get_today()
    :param date2:  时间str
    :return:
    # 比较两个日期，如果data1>data2则返回True否则为False
    """
    return datetime.datetime.strptime(date1, '%Y-%m-%d') > datetime.datetime.strptime(date2, '%Y-%m-%d')


def remove_tags(response, tag, *args):  # 删除response标签
    """
    # response tag删除(适配情况少，目前仅仅可删除非嵌套标签，慎用)
    :param response: response
    :param tag: 'script' : 表示删除<script>标签
    :param args:  可添加多可变量
    :return: 删除后的tag后的response
    """
    tag_list = list()
    tag_list.append(tag)
    if args:
        for i in list(args):
            tag_list.append(i)
    for tag in tag_list:
        response = response.replace(
            body=re.sub(r'<%s.*</%s>' % (tag, tag), '', response.body.decode(response.encoding), flags=re.S))
    return response

    # for tag in tags:
    #     response = response.replace(body=re.sub(tag, '', response.body.decode(response.encoding), flags=re.S))
    # return response


# 以下为解析各类表格的方法，需要结合实际情况使用，最常用的是get_table_datas(table)
def clean(list_data):
    """
    数据清洗
    :param list_data:
    :return:
    """
    new_list_data = list()
    for data in list_data:
        if data is None:
            data = ''
        else:
            if isinstance(data, unicode) or isinstance(data, str):
                data = data.strip()
        new_list_data.append(data)
    return new_list_data


def get_heads(table):
    """
    获取表格标题信息
    :param table:
    :return:
    """
    heads = list()
    sub_tds = table.xpath('.//tr[2]/td')
    idx = 0
    for td in table.xpath('.//tr[1]/td'):
        main_h = td.xpath('string(.)').extract_first().strip()
        colspan = td.xpath('./@colspan').extract_first()
        if colspan is not None:
            i = 0
            while i < int(colspan):
                heads.append(main_h + '_' + sub_tds[idx].xpath('string(.)').extract_first().strip())
                i += 1
                idx += 1
        else:
            heads.append(main_h)
    return heads


def get_table_datas(table):
    """
    获取表格数据
    :param table:
    :return:
    """
    table_datas = list()
    heads = table.xpath(".//tr[1]//td").xpath("string(.)").extract()
    heads = clean(heads)
    trs = table.xpath(".//tr[position()>1]")
    for tr in trs:
        datas = tr.xpath(".//td").xpath("string(.)").extract()
        datas = clean(datas)
        # 表格无数据
        if len(datas) < len(heads):
            return table_datas
        table_datas.append(dict(zip(heads, datas)))
    return table_datas


def get_table_datas_h(table):
    """
    获取横式表格数据
    :param table:
    :return:
    """
    tds = table.xpath('.//td')
    i = 0
    table_dict = dict()
    while i < len(tds):
        title = tds[i].xpath('string(.)').extract_first()
        if title is not None and len(title.strip()) > 0:
            title = title.strip()
            data = tds[i + 1].xpath('string(.)').extract_first()
            data = data.strip() if data is not None else ''
            table_dict.update({title: data})
        i += 2
    return table_dict


def get_table_datas_with_ul(div):
    """
    获取列表数据,以ul+div的方式展现的
    :param div:
    :return:
    """
    table_datas = list()
    heads = div.xpath('./ul//li/text()').extract()
    heads = clean(heads)
    for div_p in div.xpath('./div[@class="current_p"]'):
        datas = div_p.xpath('./ul/li').xpath('string(.)').extract()
        datas[-1] = div_p.xpath('./div').xpath('string(.)').extract()
        datas = clean(datas)
        table_datas.append(dict(zip(heads, datas)))
    return table_datas


def get_table_datas_with_colspan(table):
    """
    获取带合并单元格的表格数据，结合自己的情况使用
    :param table:
    :return:
    """
    table_datas = list()
    heads = get_heads(table)
    heads = clean(heads)
    trs = table.xpath(".//tr[position()>2]")
    for tr in trs:
        datas = tr.xpath(".//td").xpath("string(.)").extract()
        datas = clean(datas)
        # 表格无数据
        if len(datas) < len(heads):
            return table_datas
        table_datas.append(dict(zip(heads, datas)))
    return table_datas


def get_table(div):
    """
    获取表格数据,head以div形式
    :param div:
    :return:
    """
    table_data = list()
    heads = div.xpath('./div[1]//td').xpath('string(.)').extract()
    heads = clean(heads)
    for tr in div.xpath('./div[2]//tr'):
        datas = tr.xpath('./td').xpath('string(.)').extract()
        datas = clean(datas)
        table_data.append(dict(zip(heads, datas)))
    return table_data


def get_table_infos(div):
    """
    获取表格数据，head有合并单元格
    :param div:
    :return:
    """
    table_datas = list()
    heads = get_heads(div.xpath('./div[@class="tab_title"]/table'))
    heads = clean(heads)
    for div_p in div.xpath('./div[@class="current_p"]'):
        datas = div_p.xpath('./ul/li').xpath('string(.)').extract()
        datas = clean(datas)
        table_datas.append(dict(zip(heads, datas)))
    return table_datas


def table_to_list(table):
    """
    # table转为list，此方法通用性较好，但展示效果为类似csv格式
    :param table:
    :return:
    """
    return [[i.strip() for i in line] for line in list(dict_to_list(table_to_dict(table)))]


def table_to_dict(table):
    """
    param table: 参数table为表格的selector
    return: 将table转为二维表，返回defaultdict数据结构类型
    """
    result = defaultdict(lambda: defaultdict(str))
    for row_i, row in enumerate(table.xpath('.//tr')):
        for col_i, col in enumerate(row.xpath('.//td|.//th')):
            colspan = col.xpath('./@colspan').extract_first()
            colspan = int(colspan) if colspan else 1
            rowspan = col.xpath('./@rowspan').extract_first()
            rowspan = int(rowspan) if rowspan else 1
            col_data = ''.join(col.xpath('.//text()').extract())
            while row_i in result and col_i in result[row_i]:
                col_i += 1
            for i in range(row_i, row_i + rowspan):
                for j in range(col_i, col_i + colspan):
                    result[i][j] = col_data
    return result


def dict_to_list(dct):
    """
    param dct: 参数dct为二维表的defaultdict数据类型
    return: 返回一个可迭代对象
    """
    for i, row in sorted(dct.items()):
        cols = []
        for j, col in sorted(row.items()):
            cols.append(col)
        yield cols


def random_delay():
    """
    随机延时
    :return:
    """
    time.sleep(random.choice([1, 2, 3]))


# 返回selector
def get_response(url):
    """
    利用requests请求返回scrapy Selector
    :param url:
    :return:
    """
    req = requests.get(url, headers={'User-Agent': random.choice(WEB_USER_AGENT)})
    response = HtmlResponse(url, body=req.content, request=req)
    selector = Selector(response)
    return selector


def get_response_post(url, data):
    """
    利用requests请求返回scrapy Selector
    :param url:
    :return:
    """
    random_delay()
    req = requests.post(url, data=data, headers={'User-Agent': random.choice(WEB_USER_AGENT)})
    response = HtmlResponse(url, body=req.content, request=req)
    selector = Selector(response)
    return selector


# 以下为序列化存储与肚去
def dump_code(file_path, code_dict):
    """
    将指定schema持久化到本地
    :return:
    """
    with open(file_path, 'w') as f:
        pickle.dump(code_dict, f)


def load_code(file_path):
    """
    加载持久化的schema
    :return:
    """
    with open(file_path, 'r') as f:
        return pickle.load(f)


def loads_last_date(file_name):
    """
    加载文档中记录的最新时间
    :param file_name:
    :return:
    """
    with open(file_name, 'r') as f:
        return f.read()


def write_last_date(file_name, last_date):
    """
    写入新的最新抓取时间
    :param file_name:
    :param last_date:
    :return:
    """
    with open(file_name, 'w') as f:
        f.write(last_date)


def is_new(last_date, cur_date):
    """
    检测当前URL是否需要抓取
    :param last_date: 上一次抓取的最新发布日期
    :param cur_date: 当前链接对应的发布日期
    :return:
    """
    if cur_date > last_date:
        return True
    else:
        return False


def is_new_short(last_date, cur_date):
    last_date_list = re.findall(r'\d+', last_date)
    cur_date_list = re.findall(r'\d+', cur_date)
    last_date_new = '-'.join(['0' + d if len(d) == 1 else d for d in last_date_list])
    cur_date_new = '-'.join(['0' + d if len(d) == 1 else d for d in cur_date_list])
    return is_new(last_date_new, cur_date_new)


# 以下为下载后文件优化方法
def dup_filter(f_name, out_file):
    """
    # 重复过滤，f_name为json文件，输出文件为爬取数据url，可用于去重
    :param f_name:
    :param out_file:
    :return:
    """
    urls = set()
    with open(f_name, 'r') as f, open(out_file, 'a') as fo:
        for line in f.readlines():
            data = json.loads(line.strip())
            url = data['download_config']['url']
            if url not in urls:
                urls.add(url)
                fo.write(line)


def filter_bad(f_name, out_file):
    """
    # 去除错误数据，正文为空，且不存在附件或者附件下载错误的
    :param f_name:
    :param out_file:
    :return:
    """
    with open(f_name, 'r') as f, open(out_file, 'a') as fo:
        for line in f.readlines():
            data = json.loads(line.strip())
            data = data['download_data']['parsed_data']
            if len(data['attachment']) != len(data['annex']) or (
                    len(data['attachment']) == 0 and len(data['articleBody']) == 0):
                continue
            fo.write(line)


def dump_urls(f_name, out_file):
    """
    # url序列化存储
    """
    urls = set()
    with open(f_name, 'r') as f, open(out_file, 'a') as fo:
        for line in f.readlines():
            data = json.loads(line.strip())
            url = data['download_config']['url']
            urls.add(url)
        pickle.dump(urls, fo)


def get_cap_url():
    chars = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A',
             'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
             'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y',
             'Z', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k',
             'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w',
             'x', 'y', 'z']
    nums = ''
    for i in range(32):
        _id = int(random.random() * 61)
        nums += chars[_id]
    random_num = str(random.random()) + str(random.randint(1000, 9999))
    url = "http://zhixing.court.gov.cn/search/captcha.do?captchaId=" + str(nums) + "&random=" + random_num
    return [nums, random_num, url]


def get_cap_img(img_url):
    r = requests.get(img_url)
    img_path = './result/seccode.jpeg'
    with open(img_path, 'wb') as f:
        im = r.content
        f.write(im)
    # seccode = raw_input('请输入验证码')
    # return seccode
    return r.content


def refresh_cap():
    captcha = get_cap_url()
    img_path = '../result/seccode.jpeg'
    cap_url = captcha[2]
    cap_num = get_cap_img(cap_url)
    print(u'您输入的是' + cap_num)
    captchaId = captcha[0]
    pCode = cap_num
    with open(img_path, 'wb') as f:
        im = r.content
        f.write(im)
    seccode = raw_input('请输入刷新验证码:')
    return seccode


import time
from hashlib import md5
import requests


class RClient(object):
    def __init__(self, username, password, soft_id, soft_key):
        self.username = username
        self.password = md5(password.encode('utf-8')).hexdigest()
        self.soft_id = soft_id
        self.soft_key = soft_key
        self.base_params = {
            'username': self.username,
            'password': self.password,
            'softid': self.soft_id,
            'softkey': self.soft_key,
        }
        self.headers = {
            'Connection': 'Keep-Alive',
            'Expect': '100-continue',
            'User-Agent': 'ben',
        }

    def rk_create(self, im, im_type, timeout=60):
        """
        im: 图片字节
        im_type: 题目类型
        """
        params = {
            'typeid': im_type,
            'timeout': timeout,
        }
        params.update(self.base_params)
        files = {'image': ('a.jpg', im)}
        r = requests.post(
            'http://api.ruokuai.com/create.json',
            data=params,
            files=files,
            headers=self.headers)
        return r.json()

    def rk_report_error(self, im_id):
        """
        im_id:报错题目的ID
        """
        params = {
            'id': im_id,
        }
        params.update(self.base_params)
        r = requests.post(
            'http://api.ruokuai.com/reporterror.json',
            data=params,
            headers=self.headers)
        return r.json()


def verify_capture():
    rc = RClient('Fighter1349', '77587758', '120931',
                 'ff52edab699e48558d18d0d70caf7d11')
    i = 0
    while True:
        try:
            cap = get_cap_url()
            captchaId = cap[0]
            img_url = cap[2]
            content = get_cap_img(img_url)
            # print captchaId, img_url
            results = rc.rk_create(content, 3040)
            # print(results)
            pCode = results.get('Result', '')
            im_id = results.get('Id', '')
            # print captchaId, pCode
            formdata = {'captchaId': captchaId, 'pCode': pCode}
            # 待测试，如果不行就要放到中间件中去请求
            r = requests.post(
                url='http://zhixing.court.gov.cn/search/checkyzm?captchaId={}&pCode={}'.format(captchaId, pCode),
                data=formdata)
            if r.text.strip() == '1':
                print(u'验证码识别正确')
                return captchaId, pCode
            else:
                print(u'验证码识别错误')
                rc.rk_report_error(im_id)
                raise ValueError
        # 如果出现问题就继续请求，最大请求三次
        except Exception as e:
            print('fuck', e)
            if i < 3:
                i += 1
                time.sleep(1)
                continue
            else:
                break


if __name__ == '__main__':
    # rc = RClient('Fighter1349', '77587758', '1',  # '120931'  'ff52edab699e48558d18d0d70caf7d11'
    #              'b40ffbee5c1cf4e38028c197eb2fc751')
    # from io import BytesIO
    #
    # f = BytesIO()
    # img_url = get_cap_url()[2]
    # r = requests.get(img_url)
    # print(r.content)
    # print(rc.rk_create(r.content, 3040))
    # img_path = '../result/seccode.jpeg'
    # with open(img_path, 'wb') as f1:
    #     im = r.content
    #     f1.write(im)
    # im = open('../result/seccode.jpeg', 'rb').read()
    # print(im)
    # print(verify_capture())
    verify_capture()

    # im = open('../result/seccode.jpeg', 'rb').read()
    # print(rc.rk_create(im, 3040))
    # print(verify_capture(
    #     'http://zhixing.court.gov.cn/search/captcha.do?captchaId=aaac64fc6ee14628bd7669101d472131&random=0.8359736712767782'))
    # print(get_cap_url())
    # pass
    # dup_filter('../result/nhfpc_20181012_2.json',
    #            '../result/nhfpc_20181012_3.json')
    # print(get_today_date())

    # dump_urls('../result/nhfpc_20181012_1.json',
    # '../result/nhfpc_urls.pkl')
    # print(cmp_date(get_yesterday(1), '2018-12-25'))
    # print(datetime.datetime.strptime('2018-9-01', '%Y-%m-%d'))
