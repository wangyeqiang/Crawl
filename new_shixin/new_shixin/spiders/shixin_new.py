# -*- coding: utf-8 -*-
import scrapy
import json
import sys
from ..items import NewShixinItem
from ..hz_tools import get_today, get_cap_url, get_cap_img, verify_capture
from ..settings import BOT_NAME as project
from copy import deepcopy

reload(sys)
sys.setdefaultencoding("utf-8")


class ShixinNewSpider(scrapy.Spider):
    name = 'shixin_new'
    meta_version = 'v1.0'
    result_dir = './result'
    allowed_domains = ['zhixing.court.gov.cn']
    custom_settings = {
        'LOG_LEVEL': 'INFO',
        # 'LOG_FILE': ''{0}/{1}_{2}_{3}.log'.format(result_dir, project, name, get_today()),
        'CONCURRENT_REQUESTS': 16,
        'DOWNLOAD_DELAY': 0.5,
        # 'HTTPCACHE_ENABLED': True,
        # AUTOTHROTTLE_ENABLED = True
        # 'FILES_STORE': '/home/ubuntu/attachment/{0}/{1}/{2}'.format(get_today(), project, name),  # 线上
        # 'FILES_STORE': '{0}/attachment/{1}/{2}/{3}'.format(result_dir, get_today(), project, name),  # 本地
        # 'FILES_RESULT_FIELD': "annex",
        'COOKIES_ENABLED': False,
        'ITEM_PIPELINES': {
            'new_shixin.pipelines.NewShixinPipeline': 300,
            # 'new_shixin.pipelines.MongoDBPipeline': 200,
            # 'new_shixin.pipelines.CommonFilePipeline': 150,
        },
        'SPIDER_MIDDLEWARES': {
            # 'new_shixin.spider_middlewares.MyCustomDownloaderMiddleware': 500,
        },
        'DOWNLOADER_MIDDLEWARES': {
            # 'new_shixin.middlewares.AbuyunProxyMiddleware': 543,
            'new_shixin.middlewares.VerifyCaptchaMiddleware': 544,
            # 'new_shixin.middlewares.HZChromeMiddleware': 560,
            'new_shixin.middlewares.MyUserAgentMiddleware': 520,
        },
    }

    def __init__(self):
        super(ShixinNewSpider, self).__init__()
        self.start_url = 'http://zhixing.court.gov.cn/search/'
        # 判断是否为增量任务 1为增量 0为全量
        self.add_task = 0
        self.formdata = {
            'pName': '',
            'pCardNum': '',
            'selectCourtId': '1',
            'pCode': '',
            'captchaId': '',
            'searchCourtName': '全国法院（包含地方各级法院）'.decode('utf-8'),
            'selectCourtArrange': '1',
            'currentPage': '1'
        }

    def start_requests(self):
        """
        开始请求
        :return:
        """
        for name in [u'大傻逼', u'王业强', u'李刚']:  # , u'王晶', u'张磊', u'王亮', u'李明', u'李志刚', u'张峰', u'李闯'
            if len(name) < 2 or len(name) > 50:
                continue
            formdata = {
                'pName': name,
                'pCardNum': '',
                'selectCourtId': '1',
                'pCode': '',
                'captchaId': '',
                'searchCourtName': '全国法院（包含地方各级法院）'.decode('utf-8'),
                'selectCourtArrange': '1',
                'currentPage': '1'
            }
            print(formdata, id(formdata))
            yield scrapy.FormRequest(url='http://zhixing.court.gov.cn/search/searchBzxr.do', formdata=formdata,
                                     callback=self.parse_id, dont_filter=True,
                                     meta={'formdata': formdata, 'type': 'id'})

    def parse_id(self, response):
        item = NewShixinItem()
        formdata = response.meta['formdata']
        currentPage = int(formdata['currentPage'])  # 当前解析的页面
        content = json.loads(response.text)[0]
        results = content.get('result', list())
        totalPage = int(content.get('totalPage', 1))
        if results:
            for result in results:
                id = result['id']
                caseCode = result['caseCode']
                item['id'] = id
                formdatas = {'pCode': '', 'captchaId': '', 'id': id}
                yield scrapy.Request(
                    url='http://zhixing.court.gov.cn/search/newdetail?id={}&j_captcha={}&captchaId={}&_={}',
                    callback=self.parse_detail, dont_filter=True, meta={'type': 'detail', 'formdata': formdatas}
                )
            print(response.meta['formdata']['pName'] + str(currentPage) + '/' + str(totalPage) + u'页爬取完毕')
        else:  # 如果resulets不存在表示没有查询到该人的信息
            print('没有查询到{}信息'.format(response.meta['formdata']['pName']))
        if totalPage != currentPage:
            next_page = str(currentPage + 1)
            formdata['currentPage'] = str(next_page)
            yield scrapy.FormRequest(url='http://zhixing.court.gov.cn/search/searchBzxr.do', dont_filter=True,
                                     formdata=formdata,
                                     callback=self.parse_id, meta={'formdata': formdata, 'type': 'id'})

    def parse_detail(self, response):
        print(response.text)

    def close(self, reason):
        # 可结合要求在爬虫运行结束添加相关操作
        super(ShixinNewSpider, self).close(self, reason)
