import re
from lxml import etree 
import time
from bs4 import BeautifulSoup
def list_or_empty(content, contype=None):
    assert isinstance(content, list), 'content is not list: {}'.format(content)

    if content:
        return contype(content[0]) if contype else content[0]
    else:
        if contype:
            if contype == int:
                return 0
            elif contype == str:
                return ''
            elif contype == list:
                return []
            else:
                raise Exception('only can deal int str list')
        else:
            return ''

def get_elem_text(elem):
    """抽取lxml.etree库中elem对象中文字

    Args:
        elem: lxml.etree库中elem对象

    Returns:
        elem中文字
    """
    if elem != '':
        return ''.join([node.strip() for node in elem.itertext()])
    else:
        return ''
#sub表示
def get_first_of_element(element, sub, contype=None):
    """抽取lxml.etree库中elem对象中文字

    Args:
        element: lxml.etree.Element
        sub: str

    Returns:
        elem中文字
    """
    content = element.xpath(sub)
    return list_or_empty(content, contype)

def get_article_by_search(text):
        """从搜索文章获得的文本 提取章列表信息

        Parameters
        ----------
        text : str or unicode
            搜索文章获得的文本

        Returns
        -------
        list[dict]
            {
                'article': {
                    'title': '',  # 文章标题
                    'url': '',  # 文章链接
                    'imgs': '',  # 文章图片list
                    'abstract': '',  # 文章摘要
                    'time': ''  # 文章推送时间
                },
                'gzh': {
                    'profile_url': '',  # 公众号最近10条群发页链接
                    'headimage': '',  # 头像
                    'wechat_name': '',  # 名称
                    'isv': '',  # 是否加v
                }
            }
        """
        page = etree.HTML(text)
        lis = page.xpath('//ul[@class="news-list"]/li')

        articles = []
        for li in lis:
            url = get_first_of_element(li, 'div[1]/a/@href')
            if url:
                title = get_first_of_element(li, 'div[2]/h3/a')
                imgs = li.xpath('div[1]/a/img/@src')
                abstract = get_first_of_element(li, 'div[2]/p')
                time1 = get_first_of_element(li, 'div[2]/div/span/script/text()')
                gzh_info = li.xpath('div[2]/div/a')[0]
            else:
                url = get_first_of_element(li, 'div/h3/a/@href')
                title = get_first_of_element(li, 'div/h3/a')
                imgs = []
                spans = li.xpath('div/div[1]/a')
                for span in spans:
                    img = span.xpath('span/img/@src')
                    if img:
                        imgs.append(img)
                abstract = get_first_of_element(li, 'div/p')
                time1 = get_first_of_element(li, 'div/div[2]/span/script/text()')
                gzh_info = li.xpath('div/div[2]/a')[0]

            if title is not None:
                title = get_elem_text(title).replace("red_beg", "").replace("red_end", "")
            if abstract is not None:
                abstract = get_elem_text(abstract).replace("red_beg", "").replace("red_end", "")

            time1 = re.findall('timeConvert\(\'(.*?)\'\)', time1)
            time1 = list_or_empty(time1, int)
            time1 = time.localtime(time1)
            time2 = time.strftime("%Y-%m-%d %H:%M:%S", time1)
            profile_url = get_first_of_element(gzh_info, '@href')
            headimage = get_first_of_element(gzh_info, '@data-headimage')
            wechat_name = get_first_of_element(gzh_info, 'text()')
            gzh_isv = get_first_of_element(gzh_info, '@data-isv', int)

            articles.append({
                'article': {
                    'title': title,
                    'url': url,
                    'imgs': imgs,
                    'abstract': abstract,
                    'time': time2
                },
                'gzh': {
                    'profile_url': profile_url,
                    'headimage': headimage,
                    'wechat_name': wechat_name,
                    'isv': gzh_isv,
                }
            })
        return articles



def get_article_detail(text, del_qqmusic=True, del_voice=True):
    """根据微信文章的临时链接获取明细

    1. 获取文本中所有的图片链接列表
    2. 获取微信文章的html内容页面(去除标题等信息)

    Parameters
    ----------
    text : str or unicode
        一篇微信文章的文本
    del_qqmusic: bool
        删除文章中的qq音乐
    del_voice: bool
        删除文章中的语音内容

    Returns
    -------
    dict
    {
        'content_html': str # 微信文本内容
        'content_img_list': list[img_url1, img_url2, ...] # 微信文本中图片列表
    }
    """
    # 1.获取文本
    html_obj = BeautifulSoup(text, "lxml")
    content_title = html_obj.find('h2',{'class':'rich_media_title'})
    
    content_text = html_obj.find('div', {'class': 'rich_media_content', 'id': 'js_content'})
    if content_text:
        # 2. 删除部分标签
        if del_qqmusic:
            qqmusic = content_text.find_all('qqmusic')
            for music in qqmusic:
                music.parent.decompose()

        if del_voice:
            # voice是一个p标签下的mpvoice标签以及class为'js_audio_frame db'的span构成，所以将父标签删除
            voices = content_text.find_all('mpvoice')
            for voice in voices:
                voice.parent.decompose()

        # 3. 获取所有的图片 [img标签，和style中的background-image]
        all_img_set = set()
        all_img_element = content_text.find_all('img')
        for ele in all_img_element:
            img_url = ele.attrs['data-src']
            del ele.attrs['data-src']

            if img_url.startswith('//'):
                img_url = 'http:{}'.format(img_url)

            ele.attrs['src'] = img_url

            if not img_url.startswith('http'):
                raise WechatSogouException('img_url [{}] 不合法'.format(img_url))
            all_img_set.add(img_url)

        backgroud_image = content_text.find_all(style=re.compile("background-image"))
        for ele in backgroud_image:
            if ele.attrs.get('data-src'):
                img_url = ele.attrs['data-src']
                if img_url.startswith('//'):
                    img_url = 'http:{}'.format(img_url) 
            
                if not img_url:
                    continue
            all_img_set.add(img_url)

        # 4. 返回数据
        all_img_list = list(all_img_set)
        content_html = content_text.get_text()
        content_title = content_title.get_text().strip()
    else:
        content_html = ''
        all_img_list = []

    return {
        'content_title':content_title,
        'content_html': content_html,
        'content_img_list': all_img_list

    }




