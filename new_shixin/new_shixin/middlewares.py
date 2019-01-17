# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/spider-middleware.html
from hz_tools import verify_capture
import re


class VerifyCaptchaMiddleware(object):
    def __init__(self):
        self.captchaId = ''
        self.pCode = ''
        self.captchaId, self.pCode = verify_capture()
        self.flag = 1  # flag代表当前验证码是否可用
        self.processing = 0  # 是否在处理验证码

    def process_request(self, request, spider):
        if self.flag == 1:  # 如果当前验证码可用
            if request.meta['type'] == 'id':
                new_body = re.sub(r'pCode=(.*?)&', 'pCode={}&'.format(self.pCode), request.body)
                new_body = re.sub(r'captchaId=(.*?)&', 'captchaId={}&'.format(self.captchaId), new_body)
                request._set_body(new_body)
            elif request.meta['type'] == 'detail':
                print(request.url)
                request._set_url(
                    'http://zhixing.court.gov.cn/search/newdetail?id={}&j_captcha={}&captchaId={}&_={}'.format(request.meta['formdata']['id'], self.pCode, self.captchaId, int(time.time() * 1000)))
                print(request.url)
            else:
                return
            request.meta['formdata'].update({'pCode': self.pCode, 'capthcaId': self.captchaId})  # 更新meta
        else:
            if self.processing == 1:  # 只有第一个失效的验证码，去验证
                self.captchaId, self.pCode = verify_capture()
                request.meta['verify_times'] += 1
                self.flag = 1
                self.processing = 0
            else:
                print('我是后来失效的验证码,但是前面刷新了，我就不管了')
            rty_request = request.copy()
            return rty_request

    # def process_exception(self, request, exception, spider):
    #     retry_req = request.copy()
    #     retry_req.dont_filter = True
    #     return retry_req

    def process_response(self, request, response, spider):
        if response.text.strip() == 'error' or response.text == {}:  # 如果返回结果正常，那么就返回response
            # 失效后，如果这个请求的验证码是最新的验证码就去验证，如果不是最新的验证码就不用验证了
            if request.meta['formdata']['pCode'] == self.pCode:  # 这个地方阻塞后失效的验证码
                request.meta['verify_times'] = request.meta.get('verify_times', 0)
                if request.meta['verify_times'] >= 3:  # 同一个请求如果超出3次去识别验证码则，忽略她
                    print('忽略请求'.format(request.meta['formdata']['pName']))
                    raise IgnoreRequest
                self.flag = 0
                # 如果返回结果为error,那就看是否为第一个出现错误的，第一个错误去识别验证码，其他的还继续原地打转
                self.processing += 1  # 这个地方解决阻塞前失效的验证码
                print('我是第{}个失效的验证码:'.format(self.processing) + self.pCode)
            else:
                print('我是在阻塞之后失效的验证码{}，新的验证码是{}'.format(request.meta['formdata']['pCode'], self.pCode))
            rty_request = request.copy()
            return rty_request

        else:
            return response


from scrapy.downloadermiddlewares.useragent import UserAgentMiddleware
import random


class MyUserAgentMiddleware(UserAgentMiddleware):
    """
    设置User-Agent
    """

    def __init__(self, user_agent):
        self.user_agent = user_agent

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            user_agent=crawler.settings.get('WEB_USER_AGENT')  # 手机端将WEB改为PHONE
        )

    def process_request(self, request, spider):
        agent = random.choice(self.user_agent)
        request.headers['User-Agent'] = agent


import base64
import logging


class AbuyunProxyMiddleware(object):
    """
     阿布云代理
    """

    def __init__(self, server, user, password):
        self.logger = logging.getLogger('scrapy.proxies')
        self.proxy_server = server
        self.proxy_auth = "Basic " + base64.b64encode(user + ":" + password)

    @classmethod
    def from_crawler(cls, crawler):
        server = 'http://proxy.abuyun.com:9020'
        user = "H54A259N5V7U724D"
        password = "3E3D91FD6089DD2E"
        return cls(server, user, password)

    def process_request(self, request, spider):
        request.meta["proxy"] = self.proxy_server
        request.headers["Proxy-Authorization"] = self.proxy_auth

    def process_exception(self, request, exception, spider):
        if 'proxy' not in request.meta:
            return
        retry_req = request.copy()
        retry_req.dont_filter = True
        return retry_req

    def process_response(self, request, response, spider):
        if request.meta.get('dont_retry', False):
            return response
        return response


import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from scrapy.exceptions import IgnoreRequest
from scrapy.http import HtmlResponse
from scrapy import signals


class HZChromeMiddleware(object):
    """
    ChromdeDriver下载中间件
    """

    def __init__(self, settings):
        self.chrome_driver_path = '/home/ubuntu/ruyi-scrapy-new/_tools/linux/chromedriver'  # 线上运行
        self.chrome_driver_path = settings.get('CHROME_DRIVER_PATH', "chromedriver")  # 本地测试使用
        options = webdriver.ChromeOptions()
        # 设置无图加载 1 允许所有图片; 2 阻止所有图片; 3 阻止第三方服务器图片
        prefs = {'profile.default_content_setting_values': {'images': 2}}
        options.add_experimental_option('prefs', prefs)
        # 设置无头浏览器
        options.add_argument('--headless')
        options.add_argument(
            'user-agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"')
        self.browser = webdriver.Chrome(executable_path=self.chrome_driver_path, chrome_options=options)

    @classmethod
    def from_crawler(cls, crawler):
        s = cls(crawler.settings)
        crawler.signals.connect(s.spider_closed, signal=signals.spider_closed)
        return s

    def process_request(self, request, spider):
        # 如果meta中Webdriver为False则不经过Webdriver中间件,默认为True
        # if request.meta.get('webdriver', True):
        #     return
        try:
            # spider.logger.info('Chromedriver start crawl : '+request.url)
            self.browser.get(request.url)
            body = self.browser.page_source
            # 设置强制等待时间
            time.sleep(2)
            # 设置隐式等待5s
            # self.browser.implicitly_wait(5)
            # 设置显式等待(建议使用)
            # element = WebDriverWait(self.browser, 15).until(
            #     ec.presence_of_element_located((By.XPATH, '//div[@class="container company_container"]')))
        except Exception as e:
            spider.logger.error('request wrong is {}'.format(str(e)))
            body = 'error'
            spider.logger.error('Ignore request, url: {}'.format(request.url))
            raise IgnoreRequest()
        finally:
            return HtmlResponse(request.url, body=body, encoding='utf-8', request=request)

    def spider_closed(self, spider):
        """Shutdown the driver when spider is closed"""
        spider.logger.info('Quit Chromedriver')
        self.browser.quit()
