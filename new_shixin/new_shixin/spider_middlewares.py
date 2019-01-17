#!/usr/bin/env python
# encoding: utf-8

"""
@version: 1.0
@file: downloaDownloadMiddlewared_middleware.py
@desc: 
"""
import json
from scrapy.mail import MailSender
from scrapy.exceptions import NotConfigured


class MyCustomDownloaderMiddleware(object):

    def __init__(self, recipients, mail):
        self.recipients = recipients
        self.mail = mail

    @classmethod
    def from_crawler(cls, crawler):
        recipients = crawler.settings.getlist("MAIL_TO")
        if not recipients:
            raise NotConfigured
        mail = MailSender.from_settings(crawler.settings)
        o = cls(recipients, mail)
        return o

    def process_response(self, request, response, spider):
        return response

    def process_exception(self, request, exception, spider):
        """
        catch exceptions and send email to report
        :param request:
        :param exception:
        :param spider:
        :return:
        """
        if exception is not None:
            content = {'project_name': spider.settings.attributes['BOT_NAME'].value,
                       'spider_name': spider.name,
                       'url': request.url,
                       'failure_report': {'args': str(exception.args),
                                          'message': str(exception.message)},
                       'error_from': 'Download handler'}
            self.mail.send(self.recipients, "Scrapy Downloader Error", json.dumps(content))
        return None
