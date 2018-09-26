from collections import OrderedDict
_search_type_article = 2  # 文章
from urllib.parse import urlencode 
#拼接搜索文章
def gen_search_article_url(keyword, page=1, timesn=0,article_type='all', ft=None, et=None):       
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

        # Returns
        # -------
        # str
        #     search_article_url
        
        assert isinstance(page, int) and page > 0
        assert timesn in [0 ,#WechatSogouConst.search_article_time.anytime,
                          1, #WechatSogouConst.search_article_time.day,
                          2, #WechatSogouConst.search_article_time.week,
                          3, #WechatSogouConst.search_article_time.month,
                          4, #WechatSogouConst.search_article_time.year,
                          5  #WechatSogouConst.search_article_time.specific
                          ]
        #WechatSogouConst.search_article_time.specific:
        if timesn == 5:
            assert isinstance(ft, datetime.date)
            assert isinstance(et, datetime.date)
            assert ft <= et
        else:
            ft = ''
            et = ''

        interation_image = 458754
        interation_video = 458756
        if article_type == 'rich':     #WechatSogouConst.search_article_type.rich:
            interation = '{},{}'.format(interation_image, interation_video)
        elif article_type == 'image':  #WechatSogouConst.search_article_type.image:
            interation = interation_image
        elif article_type == 'video':   #WechatSogouConst.search_article_type.video:
            interation = interation_video
        else:
            interation = ''
        
        #OrderedDict()表示有序的字典    
        qs_dict = OrderedDict()
        qs_dict['type'] = _search_type_article
        qs_dict['page'] = page
        qs_dict['ie'] = 'utf8'
        qs_dict['query'] = keyword
        qs_dict['interation'] = interation
        if timesn != 0:
            qs_dict['tsn'] = timesn
            qs_dict['ft'] = str(ft)
            qs_dict['et'] = str(et)

        # TODO 账号内搜索
        # '账号内 http://weixin.sogou.com/weixin?type=2&ie=utf8&query=%E9%AB%98%E8%80%83&tsn=3&ft=&et=&interation=458754
        # &wxid=oIWsFt1tmWoG6vO6BcsS7St61bRE&usip=nanhangqinggong'
        # qs['wxid'] = wxid
        # qs['usip'] = usip
        #urlencode = urllib.parse.urlencode
        #print(qs_dict)
        return 'http://weixin.sogou.com/weixin?{}'.format(urlencode(qs_dict))