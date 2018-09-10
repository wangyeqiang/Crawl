# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class JdItem(scrapy.Item):
    # define the fields for your item here like:
    #名字
    name = scrapy.Field()
    #价格
    price = scrapy.Field()
    #店铺
    store = scrapy.Field()
    #评论条数
    evaluate_num = scrapy.Field()
    #商品url
    detail_url = scrapy.Field()
    #提供商
    support = scrapy.Field()
    

    
