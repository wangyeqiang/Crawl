# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

from io import open
import scrapy
import os
import time
from scrapy.pipelines.files import FilesPipeline
from settings import BOT_NAME
import datetime
import json
import pymongo
from scrapy.exceptions import DropItem
today = datetime.date.today().strftime('%Y%m%d')


class NewShixinPipeline(object):
    """
    json存储
    """
    def process_item(self, item, spider):
        if not os.path.exists(spider.result_dir):
            os.mkdir(spider.result_dir)
        file_name = '{}/{}_{}.json'.format(spider.result_dir, spider.name, today)
        result = {
            'meta_version': spider.meta_version,
            'meta_updated': datetime.datetime.now().isoformat()[:19],
            'download_config': {
                'url': item["url"],
                'method': 'GET'
                                },
            'download_data': {
                'parsed_data': {},
                'raw_data': {'html': item.get('raw_data', '')} if 'raw_data' in item  else {}
                            }
                  }
        for k in item.keys():
            if k in ['url', 'raw_data']:
                continue
            result['download_data']['parsed_data'][k] = item[k]
        with open(file_name, 'a', encoding='utf-8') as f:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')
        return item


class MongoDBPipeline(object):
    """
    MongoDB存储
    """
    def __init__(self):
        # self.client = pymongo.MongoClient(host='127.0.0.1', port=27017)
        # self.client = pymongo.MongoClient("mongodb://root:^aTFYU23Aqwe^@localhost:9999")  #本地访问远程数据库
        self.client = pymongo.MongoClient("mongodb://root:^aTFYU23Aqwe^@10.10.212.209")
        # 设定指定db
        self.db = self.client['news']

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        result = {
            'meta_version': spider.meta_version,
            'meta_updated': datetime.datetime.now().isoformat()[:19],
            'download_config': {
                'url': item["url"],
                'method': 'GET'
            },
            'download_data': {
                'parsed_data': {},
                'raw_data': {'html': item.get('raw_data', '')} if 'raw_data' in item  else {}
            }
                }
        # 设定指定collection
        table = self.db['{}_'.format(BOT_NAME) +  spider.name]
        for k in item.keys():
            if k in ['url', 'raw_data']:
                continue
            result['download_data']['parsed_data'][k] = item[k]
        table.insert(result)
        return item


class CommonFilePipeline(FilesPipeline):
    """
    下载附件
    """
    def get_media_requests(self, item, info):
        for x in item.get('attachment', []):
            yield scrapy.Request(
                url=x['url'],
                meta={'source': info.spider.name, 'name': x['name']},
            )

    def file_path(self, request, response=None, info=None):
        time_now = datetime.datetime.now().strftime('%Y%m%d')
        pre = "{}_{}".format(request.meta['source'], time_now)
        media_guid = request.meta['name']
        media_ext = os.path.splitext(request.url)[1]
        # 结合实际情况，更改
        # if len(media_ext.strip()) == 0 and 'FileWeb' in request.url:
        #    media_ext = str(time.time()).replace('.', '') + '.pdf'
        return '%s/%s%s' % (pre, media_guid, media_ext)



