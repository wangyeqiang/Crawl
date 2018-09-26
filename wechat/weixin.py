#absolute_import 绝对引用 ，unicode_literals为了python版本兼容性，print_function py2和py3打印形式得劲兼容
from __future__ import absolute_import, unicode_literals, print_function
import re
import time
import requests
#不显示提示
requests.packages.urllib3.disable_warnings()
import pymongo
from collections import OrderedDict
import datetime
from urllib.parse import urlencode as urlencode
from lxml import etree
from exceptions import WechatSogouRequestsException, WechatSogouVcodeOcrException, WechatSogouException
from parse_html import get_article_by_search,get_article_detail
from identify_image import identify_image_callback_by_hand
from identify_image import unlock_sogou_callback_example
from request import gen_search_article_url
from filecache import WechatCache
ws_cache = WechatCache()

class sougouweixin(object):
    def __init__(self,captcha_break_time=1, **kwargs):
        """初始化参数

        Parameters
        ----------
        captcha_break_time : int
            验证码输入错误重试次数
        proxies : dict
            代理
        timeout : float
            超时时间
        """
        self.client = pymongo.MongoClient('192.168.186.128',27017) #写入数据库，本地的将ip改为localhost
        scrapy_db = self.client['weixin']       # 创建数据库
        self.coll = scrapy_db['weixn_article']      # 创建数据库中的表格

        assert isinstance(captcha_break_time, int) and 0 < captcha_break_time < 20
        #验证码输入错误次数
        self.captcha_break_times = captcha_break_time
        #额外参数可以设置代理
        self.requests_kwargs = kwargs
   
    #当触发验证码的时候，要传递cookie值，解锁验证码__set__cookie,__set__cache,__unlock__sogou三个函数为处理验证码时候cookie值的传递
    def __set_cookie(self,suv=None, snuid=None, referer=None):
        #那也就是说如果没有出现验证码的情况下,suv和snuid都为空，因为没有设置
        suv = ws_cache.get('suv') if suv is None else suv
        snuid = ws_cache.get('snuid') if snuid is None else snuid
        _headers = {'Cookie': 'SUV={};SNUID={};'.format(suv, snuid)}
        if referer is not None:
            _headers['Referer'] = referer
        return _headers
    def __set_cache(self,suv,snuid):
        ws_cache.set('suv', suv)
        ws_cache.set('snuid', snuid)
    def __unlock_sogou(self,url, resp, session, unlock_callback=None, identify_image_callback=None):
        if unlock_callback is None:
            unlock_callback = unlock_sogou_callback_example
        millis = int(round(time.time() * 1000))
        #这个r_captcha.content就是img图片
        r_captcha = session.get('http://weixin.sogou.com/antispider/util/seccode.php?tc={}'.format(millis))
        if not r_captcha.ok:
            raise WechatSogouRequestsException('WechatSogouAPI get img', resp)
        #unlock_callback为unlock_sogou_callback_example,r_unlock返回的为手动输入的验证码，identify_image_callback为identify_image_callback_by_hand
        r_unlock = unlock_callback(url, session, resp, r_captcha.content, identify_image_callback)

        if r_unlock['code'] != 0:
            raise WechatSogouVcodeOcrException(
                '[WechatSogouAPI identify image] code: {code}, msg: {msg}'.format(code=r_unlock.get('code'),
                                                                                  msg=r_unlock.get('msg')))
        else:
            print('suid',session.cookies.get('SUID'))
            print('SNUID',r_unlock['id'])
            self.__set_cache(session.cookies.get('SUID'), r_unlock['id'])

    #这个get就是最终的请求，Headers就是__set_cookie(referer=referer))
    def __get(self,url, session, headers):
        resp = session.get(url, headers=headers,**self.requests_kwargs)
        if not resp.ok:
            raise WechatSogouRequestsException('WechatSogouAPI get error', resp)
        return resp

    #这里get_by_unlock看是否需要验证码，不需要的话直接请求，需要的话就进行需要验证码的请求
    def get_by_unlock(self,url, referer=None, unlock_platform=None, unlock_callback=None,identify_image_callback=None):
        #保证uvlock_platform可用，这里调用的__unlock_sougou
        assert unlock_platform is None or callable(unlock_platform) 
        #验证码识别用identify_image_callback_by_hand即手动识别
        if identify_image_callback is None:
            identify_image_callback = identify_image_callback_by_hand
        #断言验证码识别可用
        assert callable(identify_image_callback)    
        #断言unlock_callback可以调用或者为None，这里为None   
        assert unlock_callback is None or callable(unlock_callback)
        #建立一个session的请求 
        session = requests.session()
        #对搜索页面的网页进行请求，但是要设置headers,这里的refer还是为None
        resp =self.__get(url=url,session=session, headers=self.__set_cookie(referer=referer))
        #如果弹出验证码那个url中就带有antispider就识别验证码,在这里才需要unlock_callback和identify_image_callback
        if 'antispider' in resp.url or '请输入验证码' in resp.text:
            #for i in range(self.captcha_break_times):
            print('要输入验证码')
            for i in range(2):
                try:
                    #这个地方进入了打码平台，会进行验证码验证__unlock_sougou，unlock_callback还是None，idenfify_image_callback是identify_image_callback_by_hand
                    #resp为进入了验证码那个界面
                    unlock_platform(url, resp, session, unlock_callback, identify_image_callback)
                    break
                except WechatSogouVcodeOcrException as e:
                    if i ==  1:
                        raise WechatSogouVcodeOcrException(e)

            if '请输入验证码' in resp.text:
                resp = session.get(url)
            else:
                resp = self.__get(url, session, headers=self.__set_cookie(referer=referer))
        #没有验证码就直接返回得到的网页了
        return resp
   
    #获取搜索页面
    def search_article(self,keyword, page=1, timesn=1, article_type='all', ft=None, et=None,unlock_callback=None,identify_image_callback=None):
        #主要是构造url
        # 拼接搜索 文章 URL
        # Parameters
        # ----------
        # keyword : str or unicode
        #     搜索文字
        # page : int, optional
        #     页数 the default is 1
        # timesn : WechatSogouConst.search_article_time
        #     时间 anytime 没有限制 / day 一天 / week 一周 / month 一月 / year 一年 / specific 自定
        #     默认是 anytime
        # article_type : WechatSogouConst.search_article_type
        #     含有内容的类型 image 有图 / video 有视频 / rich 有图和视频 / all 啥都有
        #     默认是 all
        # ft, et : datetime.date
        #     当 tsn 是 specific 时，ft 代表开始时间，如： 2017-07-01
        #     当 tsn 是 specific 时，et 代表结束时间，如： 2017-07-15
        url = gen_search_article_url(keyword, page, timesn, article_type, ft, et)
        resp = self.get_by_unlock(url=url, referer = gen_search_article_url(keyword),
                                        unlock_platform=self.__unlock_sogou, #这个是自带的
                                        unlock_callback=unlock_callback, #None 
                                        identify_image_callback=identify_image_callback) #None        
        return get_article_by_search(resp.text)

    
    def write_mongo(self,data):
        self.coll.insert_one(dict(data))



if __name__== "__main__":
    #阿布云代理IP
    proxyHost = "http-dyn.abuyun.com"
    proxyPort = "9020"
    #代理隧道验证信息
    proxyUser = "H85FDL2G2E43NS4D"
    proxyPass = "B00CF7A92336694B"
    proxyMeta = "http://%(user)s:%(pass)s@%(host)s:%(port)s" % {
      "host" : proxyHost,
      "port" : proxyPort,
      "user" : proxyUser,
      "pass" : proxyPass
    }
    proxies = {
    "http"  : proxyMeta,
    "https" : proxyMeta
    }

    sw = sougouweixin()
     # 拼接搜索 文章 URL
        # Parameters
        # ----------
        # keyword : str or unicode
        #     搜索文字
        # page : int, optional
        #     页数 the default is 1
        # timesn : WechatSogouConst.search_article_time
        #     时间 0anytime 没有限制 / 1day 一天 / 2week 一周 / 3month 一月 / 4year 一年 / 5specific 自定
        #     默认是 anytime
        # article_type : WechatSogouConst.search_article_type
        #     含有内容的类型 image 有图 / video 有视频 / rich 有图和视频 / all 啥都有
        #     默认是 all
        # ft, et : datetime.date
        #     当 tsn 是 specific 时，ft 代表开始时间，如： 2017-07-01
        #     当 tsn 是 specific 时，et 代表结束时间，如： 2017-07-15
    a =sw.search_article(keyword='北京大学',page=1,timesn=2,article_type='all')
    print(a)
   
    for i in a:
        url = i['article']['url']
        try:
            text = requests.get(url,timeout=10).text
            b = get_article_detail(text)
            print(b)
            sw.write_mongo(b)
            time.sleep(5)
        except Exception as E:
            print(E)

