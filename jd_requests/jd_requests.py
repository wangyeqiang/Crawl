import requests
requests.packages.urllib3.disable_warnings()
from lxml import etree
import time
import random
from multiprocessing.dummy import Pool
import re
import pymongo
#from multiprocessing.dummy import Pool
#获取京东商品详情页
class jd():
    def __init__(self):
        #self.url = "https://search.jd.com/Search?keyword=手机&enc=utf-8&qrst=1&rt=1&stop=1&vt=2&wq=手机&psort=4&page={}"
        self.user_agents = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1"
        self.client = pymongo.MongoClient('192.168.186.128',27017) #写入数据库，本地的将ip改为localhost
        scrapy_db = self.client['jd_requests']       # 创建数据库
        self.coll = scrapy_db['requests_phone']      # 创建数据库中的表格
    
    #解析前半页
    def parse_index(self,url):
        try:
            headers = {'User-Agent':self.user_agents}
            response = requests.get(url, headers=headers,verify = False,timeout=15)
            #以网页编码方式解码
            response.encoding = response.apparent_encoding
            time.sleep(random.randint(1, 2))
            #print(response.text)
            if response.status_code == 200:
                return response.text
            else:
                return None
        except Exception as E:
            #print(str(E))
            return None
    #通过首前半页获取商品详情页url(只有一半的商品url，后半段是通过异步加载的方式加载)；获取商品data-pid，构造后半段商品url
    def get_goods_url(self,response):
        pre_goods_url_list = []
        if response:
            html = etree.HTML(response)
        else:
            print('前半页爬取失败')
            return 
        products = html.xpath('//ul[@class="gl-warp clearfix"]/li')
        for product in products:
            goods_dic = {}
            goods_name = ''.join(product.xpath('.//div[@class="p-name p-name-type-2"]/a/em/text()')).strip().replace(' ','')
            goods_evaluate_num = product.xpath('.//div[@class="p-commit"]/strong/a/text()')[0]
            goods_dic['name'] = goods_name
            goods_dic['goods_evaluate_num'] = goods_evaluate_num
            print(goods_dic)
            self.coll.insert_one(dict(goods_dic))
        #获取前30个商品的data-pid
        goods_pid_list = html.xpath("//li[@class='gl-item']")
        if goods_pid_list:
            goods_pid = [goods_pid.get('data-pid') for goods_pid in goods_pid_list]
            #print(goods_pid,len(goods_pid))
            return goods_pid, pre_goods_url_list  
    #获取网页中后半商品的url
    def get_other_goods_url(self,pid,url):
        print(url)
        page = int(url[85:])
        #print(page)
        other_goods_url_list = []
        other_url = "https://search.jd.com/s_new.php?keyword=手机&enc=utf-8&qrst=1&rt=1&stop=1&vt=2&wq=手机&page={}&s=31&scrolling=y&log_id={}&tpl=3_M&show_items={}"
        #时间戳去掉后两位
        linux_sec = str(time.time())[:-2]
        #构造后半部分网页，有三处要除以一个page+1，一处是log_id为时间戳去掉后两位，最后的一堆列表是前半部分解析的data-pid构成的
        other_url = other_url.format(str(page+1), linux_sec, ','.join(pid))
        
        headers = {
            #refer必须带，表示又前一网页跳转过来
            'referer': 'https://search.jd.com/Search?keyword=%E6%89%8B%E6%9C%BA&enc=utf-8&qrst=1&rt=1&stop=1&vt=2&wq=%E6%89%8B%E6%9C%BA&page={}'.format(str(page)),
            'User-Agent': random.choice(self.user_agents)
        }
        
        r = requests.get(url = other_url, headers=headers,verify = False,timeout=15)
        r.encoding = r.apparent_encoding
        response = r.text
        html = etree.HTML(response)
        products = html.xpath('//li[@class="gl-item"]')
        for product in products:
            goods_dic = {}
            goods_name = ''.join(product.xpath('.//div[@class="p-name p-name-type-2"]/a/em/text()')).strip().replace(' ','')
            goods_evaluate_num = product.xpath('.//div[@class="p-commit"]/strong/a/text()')[0]
            goods_dic['name'] = goods_name
            goods_dic['goods_evaluate_num'] = goods_evaluate_num
            print(goods_dic)
            self.coll.insert_one(dict(goods_dic)) 
        print("获取后半商品url成功")

def main(url):
    response = jd.parse_index(url)
    goods_pid, pre_goods_url_list = jd.get_goods_url(response)
    jd.get_other_goods_url(pid=goods_pid,url=url)
    time.sleep(5)
    #jd.get_all_goods_url_list(pre_goods_url_list,other_goods_url_list)
if __name__ =='__main__':
    jd = jd()
    url = 'https://search.jd.com/Search?keyword=手机&enc=utf-8&qrst=1&rt=1&stop=1&vt=2&wq=手机&page={}'
    format_url = [url.format(str(i))  for i in range(1,200,2)]
    #print(format_url)
    pool = Pool(3)
    pool.map(main, format_url)
    pool.close()
    pool.join()
    time.sleep(15)
    print("数据爬取完毕")
        

        
