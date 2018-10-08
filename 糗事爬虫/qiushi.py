import requests
import urllib.request
import json
from lxml import etree

url = "https://www.qiushibaike.com/8hr/page/1/"

headers = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv2.0.1) Gecko/20100101 Firefox/4.0.1"}
request = urllib.request.Request(url,headers = headers)

# html = urllib.request.urlopen(request).read().decode("utf-8")

html = urllib.request.urlopen(request).read().decode("utf-8")
#相应返回的是字符串，解析为HTML DOM格式
text = etree.HTML(html)


#返回所有段子的节点位置，contains()模糊查询方法，contains(),第一个参数为要匹配的标签，第二个参数为标签名的部分内容
node_list = text.xpath('//div[contains(@id,"qiushi_tag")]')

items = {}
for node in node_list:
    #用户名 xpath返回的都是列表需要用下标形式取值，tag标签在最后时需要.text来确定其内容
    
    username = node.xpath('./div[@class="author clearfix"]//h2')[0].text.replace('\n','')


    #图片链接
    image = node.xpath('.//div[@class="thumb"]/a/img/@src')

    #段子内容
    # content = node.xpath('.//div[@class="content"]/span')[0].text.replace('\n','')

    content = node.xpath('.//div[@class="content"]/span')[0].extract()

    #点赞数量 text就是取出标签里包含的内容
    zan = node.xpath('.//span[@class="stats-comments"]//i')[0].text.replace('\n','')

    #评论
    comments = node.xpath('.//span[@class="stats-vote"]/i')[0].text.replace('\n','')

    items = {
        "username" :username,
        "image" :image,
        "content" :content,
        "zan" :zan,
        "comments" :comments
    }

    # print(items)
    #print(content)
    try:
        with open("qiushi.json","a") as f:
            f.write(json.dumps(items,ensure_ascii = False) + "\n")
    except:
        print('')

        1