# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class NewShixinItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    headline = scrapy.Field()   # 标题
    datePublished = scrapy.Field()  # 发布日期
    articleBody = scrapy.Field()   # 正文
    url = scrapy.Field()   # 源连接
    table = scrapy.Field()  # 表格
    attachment = scrapy.Field()   # 附件
    annex = scrapy.Field()  # 附件字段
    newsCategory = scrapy.Field()   #所属新闻板块
    copyrightHolder  = scrapy.Field()  #新闻来源字段
    raw_data = scrapy.Field() # 正文源码
    id = scrapy.Field()
    caseCode = scrapy.Field()
    pName = scrapy.Field()
    currentPage = scrapy.Field()
    totalPage = scrapy.Field()