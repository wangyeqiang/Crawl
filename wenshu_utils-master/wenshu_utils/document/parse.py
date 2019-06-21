# coding: utf-8
import re


def parse_detail(text: str) -> dict:
    group_dict = re.search(r'var caseinfo=JSON.stringify\((?P<case_info>.+?)\);\$'
                           r'.+(var dirData = (?P<dir_data>.+?);if)?'  # 2018年底改版了，dirData没有返回了
                           r'.+var jsonHtmlData = (?P<html_data>".+");',
                           text, re.S).groupdict()
    return group_dict
