# -*- coding: utf-8 -*-
import scrapy
from jd.items import JdItem


class JingdongSpider(scrapy.Spider):


    name = "jingdong"
    allowed_domains = ["search.jd.com"]
    base_url = 'https://search.jd.com/Search?keyword=%E6%89%8B%E6%9C%BA&enc=utf-8&qrst=1&rt=1&stop=1&vt=2&wq=%E6%89%8B%E6%9C%BA&cid2=653&cid3=655&psort=4&click=0' 
    page = 1
    start_urls = [base_url + '&page=' + str(page) + '&click=0']

    def start_requests(self):   
        yield scrapy.Request(url = self.base_url,callback=self.parse,meta={'page':self.page},dont_filter=True)

    def parse(self,response):
        #商品列表
        products = response.xpath('//ul[@class="gl-warp clearfix"]/li')
        #列表迭代
        for product in products:
            item = JdItem()
            try:
                name = ''.join(product.xpath('.//div[@class="p-name p-name-type-2"]/a/em/text()').extract()).strip().replace(' ','')
            except:
                name = ''
            try:
                price = product.xpath('.//div[@class="p-price"]//i/text()').extract()[0]
            except:
                price = ''

            try:
                store = product.xpath('.//div[@class="p-shop"]//a/@title').extract()[0]
            except:
                store = ''
            try:
                evaluate_num = product.xpath('.//div[@class="p-commit"]/strong/a/text()').extract()[0]
            except:
                evaluate_num = ''
            try:
                detail_url = product.xpath('.//div[@class="p-name p-name-type-2"]/a/@href').extract()[0]
            except:
                detail_url = ''
            try:
                if product.xpath('.//div[@class="p-icons"]/i/text()').extract()[0]=='自营':
                    support = '自营'
                else:
                    support = '非自营'
            except:
                support = '非自营'
                

            item['name'] = name 
            item['price'] = price
            item['store'] = store
            item['evaluate_num'] = evaluate_num
            item['detail_url'] = detail_url
            item['support'] = support
            yield item
            print(item)
        if self.page < 100:
            self.page += 1
            print(self.page)
            yield scrapy.Request(url=self.base_url,callback=self.parse,meta={'page':self.page},dont_filter=True)


