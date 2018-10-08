import requests
from lxml import etree
import time
import re
import random
import json
import jsonpath
from bs4 import BeautifulSoup
import re
import time
from multiprocessing import Manager,Pool
import multiprocessing
import socket
import pymysql
'''
爬取框架：
0、获取所有省会城市的编号
1、获取positionidid 和网址
2、获取职位详情页并解析
3、写入Mysql数据库
'''
def city_code_spider():
    global city_code_queue
    url = 'https://www.zhipin.com/common/data/city.json'
    r = requests.get(url,headers=headers,verify=False)
    r.encoding = r.apparent_encoding
    result = json.loads(r.text)
    city_list = jsonpath.jsonpath(result,'$.data.cityList')
    #print(city_list)
    #print(len(city_list[0]))
    result_list = []
    #for i in range(len(city_list[0])):
    for i in range(4,len(city_list[0])):
        province_list = jsonpath.jsonpath(city_list,'$.*'+str([i]))
        province_name = jsonpath.jsonpath(city_list,'$.*'+ str([i])+'.name')[0]
        #表示所有的城市
        #for j in range(len(province_list[0]['subLevelModelList'])):
        #表示所有的省会城市
        for j in [0]:
            city_dic = {}
            city_name = jsonpath.jsonpath(city_list,'$.*'+str([i])+'.subLevelModelList'+str([j])+'.name')[0]
            city_code = jsonpath.jsonpath(city_list,'$.*'+str([i])+'.subLevelModelList'+str([j])+'.code')[0]
            city_dic['province_name'] = province_name
            city_dic['city_name'] = city_name
            city_dic['city_code'] = city_code
            city_code_queue.put(city_dic)
            print(city_dic)

def get_end_url(city_code_queue,end_url_queue,headers,proxies):
    global f
    if not get_end_url_exit:
        while not city_code_queue.empty():
        #while True:
            city_code_list = city_code_queue.get()
            print(city_code_list)
            # province_name = city_code_list['province_name']
            # city_name = city_code_list['city_name']
            city_code = city_code_list['city_code']
            print(city_code)
            #省会python岗位的职位列表url
            url = 'https://www.zhipin.com/c'+ str(city_code) + '-p100109/' 
            for page in range(1,11):   
                params = {
                        'page':str(page),
                        'ka':'page-'+ str(page)
                }
                User_Agent_list = [
                "Mozilla/5.0 (Windows NT 6.1; rv2.0.1) Gecko/20100101 Firefox/4.0.1",
                "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/14.0.835.163 Safari/535.1",
                "Opera/9.80 (Windows NT 6.1; U; en) Presto/2.8.131 Version/11.11"
                ]
                User_Agent = random.choice(User_Agent_list)
                get_end_url_headers = headers.copy()
                get_end_url_headers.update({'User-Agent':User_Agent})
                #print(get_end_url_headers)
                try:  
                    r = requests.get(url,headers=get_end_url_headers,params = params,verify=False,timeout=15)
                    # print('当前主机的IP为: ' + socket.gethostbyname(socket.gethostname()))
                    # print (r.raw._connection.sock.getpeername()[0])
                    r.encoding = r.apparent_encoding
                    # with open('zhilian.txt','a') as f:
                    #     f.write(r.text)
                    print(r.status_code)
                except Exception as e:
                    print(e)
                    city_code_queue.put(city_code_list)
                    continue
                try:
                    result = etree.HTML(r.text)
                    #获取Jobid
                    jobids = result.xpath('//li//h3[@class="name"]/a/@data-jobid')
                    #print(jobids)
                    #获取末尾url
                    end_urls = result.xpath('//li//div[@class="info-primary"]//h3/a/@href')
                    count = 0
                    for end_url in end_urls:
                        job_id = jobids[count]
                        count+=1
                        end_url_dic = {}
                        end_url_dic['province_name'] = city_code_list['province_name']
                        end_url_dic['city_name'] = city_code_list['city_name']
                        end_url_dic['city_code'] = city_code_list['city_code']
                        end_url_dic['end_url'] = end_url
                        end_url_dic['job_id'] = job_id
                        end_urls_list.append(end_url)
                        end_url_queue.put(end_url_dic)
                        print(end_url_dic)
                        f.write(str(end_url_dic))
                except Exception as E:
                    print(E)
                time.sleep(5)    
                #f.write(end_url_dic)
    print('city_code_queue空为：' + str(city_code_queue.empty()))      

def get_job_detail(end_url_queue,headers,proxies):
    print('get_job_detail开始')
    #global get_job_detail_EXIT
    # while not get_job_detail_EXIT:
        # if end_url_queue.empty():
    global error_get_end_url_list
    while not end_url_queue.empty():
        User_Agent_list = [
                "Mozilla/5.0 (Windows NT 6.1; rv2.0.1) Gecko/20100101 Firefox/4.0.1",
                "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/14.0.835.163 Safari/535.1",
                "Opera/9.80 (Windows NT 6.1; U; en) Presto/2.8.131 Version/11.11"
                ]
        User_Agent = random.choice(User_Agent_list)
        get_job_detail_headers = headers.copy()
        get_job_detail_headers.update({'User-Agent':User_Agent})
        get_end_url_list = end_url_queue.get()
        get_end_url = get_end_url_list['end_url']
        detail_url = 'https://www.zhipin.com' + get_end_url
        try:
            r = requests.get(url=detail_url,headers=get_job_detail_headers,timeout=15,verify=False)
            r.encoding = r.apparent_encoding
            print(r.url)
            #print(r.status_code)
            result = etree.HTML(r.text)
        except Exception as e:
            print(e)
            print(r.url)
            error_get_end_url_list.append(get_end_url_list)
            if error_get_end_url_list.count(get_end_url_list) >= 3:
                continue
            else:
                end_url_queue.put(get_end_url_list)
                continue
        #获取职位名称
        try:
            job_name = result.xpath('//div[@class="name"]/h1')[0].text
        except:
            job_name = ''
        try:
            job_id = get_end_url_list['job_id']
        except:
            job_id = ''
        #获取发布时间
        try:
            job_times = result.xpath('//div[@class="job-author"]/span/text()')[0]
            job_time = job_times.split('发布于')[1]
        except:
            job_time = ''
        #获取职位薪水0\
        try:
            job_salary = result.xpath('//div[@class="info-primary"]/div[@class="name"]/span')[0].text.strip()
        except:
            job_salary = ''
        #工作地点
        try:
            job_address = result.xpath('//div[@class="info-primary"]/p/text()')[0]
        except:
            job_address =''
        #工作经验
        try:
            job_experience = result.xpath('//div[@class="info-primary"]/p/text()')[1]
        except:
            job_experience = ''
        #工作学历
        try:
            job_education = result.xpath('//div[@class="info-primary"]/p/text()')[2]
        except:
            job_education = ''
        #工作描述
        try:
            job_descriptions = result.xpath('//div[@class="detail-content"]/div[@class="job-sec"]/div[@class="text"]/text()')
            job_description = ''
            for i in range(len(job_descriptions)):
                content = job_descriptions[i].strip()
                job_description += content
        except:
            job_description = ''
        #团队介绍
        try:
            team_introduces = result.xpath('//div[@class="detail-content"]/div[@class="job-sec"]/div[@class="job-tags"]/span/text()')
            team_introduce = ','.join(str(x) for x in team_introduces)
        except:
            team_introduce = ''
        
        #公司介绍
        try:
            company_introduce = result.xpath('//div[@class="detail-content"]/div[@class="job-sec company-info"]/div[@class="text"]')[0].text.strip()
        except:
            company_introduce = ''

        params = [job_id,job_name,job_time,job_salary,job_address,job_experience,job_education,job_description]
        try:
            conn = pymysql.connect(host='localhost',port=3306,db='Boss_spider',user='root',passwd='591777',charset='utf8')
            cs1 = conn.cursor()
            count = cs1.execute("insert into job_detail(job_id,job_name,job_time,job_salary,job_address,job_experience,job_education,job_description) values(%s,%s,%s,%s,%s,%s,%s,%s)",params)
            print(count)
            conn.commit()
            cs1.close()
            conn.close()
        except Exception as e:
            print(e)
        print(job_id,job_name,job_time)
        time.sleep(1)
    print('get_job_detail结束')
if __name__ == "__main__":
    requests.packages.urllib3.disable_warnings()
    end_urls_list = []
    get_end_url_exit = False
    #get_job_detail_EXIT信号开关
    get_job_detail_EXIT = False   
    error_get_end_url_list = []
    headers = {
        "Host":"www.zhipin.com",
        "Connection":"keep-alive",
        "Cache-Control":"max-age=0",
        "Upgrade-Insecure-Requests":"1",
        #"Referer":"https://www.zhipin.com/?sid=sem_pz_bdpc_dasou_title",
        "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language":"zh-CN,zh;q=0.9,en;q=0.8"
    }
    #代理IP
    proxyHost = "http-dyn.abuyun.com"
    proxyPort = "9020"
    #代理隧道验证信息
    proxyUser = "H8P82770U1YHR33D"
    proxyPass = "709100148FA6EF36"
    proxyMeta = "http://%(user)s:%(pass)s@%(host)s:%(port)s" % {
      "host" : proxyHost,
      "port" : proxyPort,
      "user" : proxyUser,
      "pass" : proxyPass
    }
    proxies = {
    "http"  : proxyMeta,
    "https" : proxyMeta
    }
    f = open('job_list.txt','a')
    # f.close()
    #创建城市代码队列
    city_code_queue = Manager().Queue()
    #创建末尾url队列
    end_url_queue = Manager().Queue()
    #爬取城市代码网页，将所有的城市代码爬取下来，并传入队列当中，以方便接下来爬取每个城市的职位信息使用
    city_code_spider()
    #time.sleep()
    #创建进程池
    p1=Pool(2)
    #print('cpu数量为：'+str(multiprocessing.cpu_count()))
    p2= Pool(3)
    # #f = open('job_list.txt','a')
    for i in range(2):
        p1.apply_async(get_end_url,(city_code_queue,end_url_queue,headers,proxies))
        print(1)
    #get_end_url(city_code_queue,end_url_queue,headers,proxies)
    while end_url_queue.empty():
        pass
    print('继续往下执行')

    for i in range(3):
        p2.apply(get_job_detail,(end_url_queue,headers,proxies))
        print(2)
    while not end_url_queue.empty():
        pass
    get_job_detail_EXIT = True
    print('------start--------')
    while not city_code_queue.empty():
        pass
    print('队列为空了')
    p1.close()
    p2.close()
    p1.join()
    p2.join()
    #f.close()
    print('-------end------')
