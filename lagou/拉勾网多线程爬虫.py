import requests
import hashlib
import re
import json
import jsonpath
import time
import random
import threading
from queue import Queue
from lxml import etree

PARSE_EXIT = False
#登录操作
class Lagou_login(object):
    def __init__(self):
        #不提示忽略ssl信息，'verification is strongly advised.''
        requests.packages.urllib3.disable_warnings()
        #请求对象，用于保持cookies
        self.session = requests.Session()
        #请求头信息
        self.headers = {
        'Referer': 'https://passport.lagou.com/login/login.html',
        "Connection":"keep-alive",
        "Cache-Control":"max-age=0",
        "Upgrade-Insecure-Requests":"1",
        "User-Agent":"Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.117 Safari/537.36",
        "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Encoding":"gzip, deflate, br",
        "Accept-Language":"zh-CN,zh;q=0.9,en;q=0.8",
        }
    #获取Forge_Token和Forge_Code(拉勾网反爬虫手段)
    def get_token(self):
        Forge_Token = ''
        Forge_Code = ''
        #用之前的请求session继续请求登录界面
        r = self.session.get('https://passport.lagou.com/login/login.html',headers=self.headers,verify = False)
        '''
        <!-- 页面样式 -->    <!-- 动态token，防御伪造请求，重复提交 -->
        <script>
        window.X_Anti_Forge_Token = '71eebe0d-bbf4-413c-b791-445eef87c2ef';
        window.X_Anti_Forge_Code = '11626596';
        </script>
        '''
        #正则表达式解析Forge_Token，Forge_Code
        search_obj = re.search(r".*Anti_Forge_Token = '(.*?)';.*Anti_Forge_Code = '(\d+?)';",r.text,re.DOTALL)
        if search_obj:
            Forge_Token = search_obj.group(1)
            Forge_Code = search_obj.group(2)
        return Forge_Token,Forge_Code
        
    #给密码加密,在main.html_aio_bdf7227.js中可以找到，对密码用md5双重加密
    def encrypt_pwd(self,passwd):
        passwd = hashlib.md5(passwd.encode('utf-8')).hexdigest()
        
        passwd = 'veenike' + passwd + 'veenike'
        passwd = hashlib.md5(passwd.encode('utf-8')).hexdigest()
        return passwd
    
    #登录方法
    def login(self,username,passwd,proxies):
        X_Anit_Forge_Token,X_Anit_Forge_Code = self.get_token()
        login_headers = self.headers.copy()
        #在请求头信息中添加内容
        login_headers.update({'X-Anit-Forge-Token':X_Anit_Forge_Token,'X-Anit-Forge-Code':X_Anit_Forge_Code,'X-Requested-With':'XMLHttpRequest'})
        #加密密码
        password = self.encrypt_pwd(passwd)
        #传入post的数据
        post_data = {
        'isValidate':True,
        'username':username,
        'password':password,
        'request_form_verifyCode':'',
        'submit':''
        }
        #登录请求的json网页
        login_url = 'https://passport.lagou.com/login/login.json'
        #用之前的session继续请求
        r = self.session.post(login_url,headers=login_headers,data=post_data,proxies=proxies,verify=False)
        #用网页的编码方式解码
        r.coding = r.apparent_encoding
        #print(r.text)
        #返回数据中有操作成功，代表登录成功
        if r.text.find('操作成功') != -1:
            print('账户' + username + '登录成功')

#爬取python职位列表页，获取position_id
class lagou_spider(threading.Thread):
    def __init__(self,threadname,dataqueue,pagequeue,userqueue,lock,proxies):
        super(lagou_spider,self).__init__()
        self.dataqueue = dataqueue
        self.pagequeue = pagequeue
        self.lock = lock
        self.userqueue =userqueue
        self.threadname=threadname
    def run(self):
        print('启动'+self.threadname)
        #请求职位列表的json
        get_url = "https://www.lagou.com/jobs/positionAjax.json"
        #传递的参数，这里指的排序为默认，城市为深圳，params为参数
        params = {
        'px':'default',
        'city':'深圳',
        'needAddtionalResult':'false'
        }
        #请求的headers信息
        get_headers=({
            "Connection":"keep-alive",
            "X-Anit-Forge-Code":"0",
            "User-Agent":"Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.117 Safari/537.36",
            "Content-Type":"application/x-www-form-urlencoded; charset=UTF-8",
            "Accept":"application/json, text/javascript, */*; q=0.01",
            "X-Requested-With":"XMLHttpRequest",
            "X-Anit-Forge-Token":"None",
            "Referer":"https://www.lagou.com/jobs/list_Python?px=default&city=%E6%B7%B1%E5%9C%B3",
            "Accept-Encoding":"gzip, deflate, br",
            "Accept-Language":"zh-CN,zh;q=0.9,en;q=0.8"
            })
        #只要pagequeue中有数据就不断请求
        while not self.pagequeue.empty():
            #print('循环？')
            #上互斥锁，为了保证每次登录可以访问三个页面，要不然拉勾网反爬会导致错误
            with self.lock:
                user_pass = self.userqueue.get()
                #下面是为了让用户名，密码循环从队列中进出
                self.userqueue.put(user_pass)
                username = user_pass['username']
                passwd = user_pass['passwd']  
                #这里的lg是局部变量，多线程间不共用
                lg = Lagou_login()         
                lg.login(username,passwd,proxies) 
                session = lg.session

                #每个线程爬取3页，重新登录一次
                for i in range(1,4):
                    page = self.pagequeue.get()
                    #post的data
                    post_data = {
                    'first':'false',
                    'pn':str(page),
                    'kd':'python'
                    } 
                    print('当前爬取第'+str(page)+'页')
                    r = session.post(get_url,headers = get_headers,data=post_data,params = params,verify= False)

                    #将爬取内容转换为json格式
                    content = json.loads(r.text)
                    #从根节点匹配到content，使用jsonpath
                    root_code = jsonpath.jsonpath(content,'$.content.positionResult.result') 
                    #print(root_code[0])    
                    try:
                        for i in range(len(root_code[0])):
                            #从根节点result匹配当前节点天的所有节点，并取第i个的id
                            positionId = jsonpath.jsonpath(root_code,'$.*'+str([i]))[0]['positionId'] 
                            #存储id
                            self.dataqueue.put(positionId)
                            #print(positionId)
                    except:
                        pass
                    print('第'+str(page)+'页爬取结束') 
                    #这里为了保证稳定，睡眠3s，可以更少，但是没有必要，因为这里爬一页职位列表后面要爬取15页职位详情，不影响效率
                    time.sleep(3)
        print('结束'+self.threadname)

#爬取每个positionid的具体页面信息
class lagou_parse(threading.Thread):
    def __init__(self,dataqueue,threadname,filename,lock,proxies):
        super(lagou_parse,self).__init__()
        self.dataqueue = dataqueue
        self.threadname = threadname
        self.filename = filename
        self.lock = lock
        self.proxies = proxies
        self.headers={
        "Connection":"keep-alive",
        "Cache-Control": "max-age=0",
        "User-Agent":"Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.117 Safari/537.36",
        "Content-Type":"application/x-www-form-urlencoded; charset=UTF-8",
        "Upgrade-Insecure-Requests": "1",
        "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language":"zh-CN,zh;q=0.9,en;q=0.8"
        }
        self.error_list = []
    def run(self):  
        print('开始线程'+self.threadname)
        #PARSE_EXIT不退出就一直请求
        while not PARSE_EXIT:
            if not self.dataqueue.empty():
                position_id  = self.dataqueue.get()
                #print(position_id)
                #职位具体信息的网页url
                get_url = 'https://www.lagou.com/jobs/' + str(position_id)+ '.html'
                #用了try防止某个页面出错导致程序退出，
                try:
                    r = requests.get(get_url,headers=self.headers,verify=False,proxies=self.proxies)
                    #print(r.status_code)
                    content = etree.HTML(r.text)
                    #用xpath解析,可以根据自己想要的内容解析
                    #职位名称
                    position_name = content.xpath('//div[@class="job-name"]/@title')[0]
                    #薪水
                    position_slary = content.xpath('//dd[@class="job_request"]//span')[0].text
                    #要求工作经验
                    position_experience = content.xpath('//dd[@class="job_request"]//span')[2].text
                    #职位诱惑
                    position_advantage = content.xpath('//dd[@class="job-advantage"]/p')[0].text
                    #职位描述
                    position_description = ''
                    position_description_detail = content.xpath('//dd[@class="job_bt"]//p')
                    for i in range(len(position_description_detail)):
                        if position_description_detail[i].text:
                            position_description += position_description_detail[i].text.strip()   
                    #工作地点
                    position_address0 = content.xpath('//div[@class="work_addr"]/a/text()')[0]
                    position_address1 = content.xpath('//div[@class="work_addr"]/a/text()')[1]
                    position_address2 = content.xpath('//div[@class="work_addr"]/text()')[2].strip()
                    position_address = position_address0 + position_address1 + position_address2                 
                    #总结成一个字典            
                    position = { 
                                '职位id': position_id,    
                                '职位名称':position_name,
                                '职位薪水':position_slary,
                                '经验要求':position_experience,
                                '职位诱惑':position_advantage,
                                '职位描述':position_description,
                                '工作地点':position_address
                                }
                    print(position)
                    #with代表打开关闭互斥锁，为了保证写入数据不混乱，要加上锁
                    with self.lock: 
                        self.filename.write(str(position) + '\n')
                    #睡1s，小心被封- -  
                    time.sleep(1)
                except Exception as result:
                    #得到出异常的ID
                    print(str(position_id)+'出异常了')
                    print('异常为以下:\n'+ str(result))
                    self.error_list.append(position_id)
                    #遍历一下出错列表的id，如果出错三次那么就不再加入队列
                    for i in set(self.error_list):
                        if self.error_list.count(i) < 4:
                            #将出错的职位id继续加入队列
                            self.dataqueue.put(position_id)
        print('结束线程'+self.threadname)

if __name__ == "__main__":  
    #main() 
   
    #代理服务器
    proxyHost = "http-dyn.abuyun.com"
    proxyPort = "9020"
    #代理隧道验证信息
    proxyUser = "HE765V698894E95D"
    proxyPass = "C80B13A85EE12285"
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
    user_pass1 = {'username':'账号1','passwd':'密码'}
    user_pass2 = {'username':'账号2','passwd':'密码'}
    userqueue = Queue()
    userqueue.put(user_pass1)
    userqueue.put(user_pass2)

    #创建爬取数据的队列
    dataqueue = Queue() #在采集进程中put，在解析进程中get
    #创建页码队列，在页码队列中添加20个页码
    pagequeue = Queue()
    for i in range(1,21):
        pagequeue.put(i)
    #打开文件filename
    filename = open('lagou.txt','a')
    #创建互斥锁
    lock = threading.Lock()
    lock2 = threading.Lock()
    
    #采集队列，这里放两个就好，放多了代理的session会混乱
    Spider_list = ['爬取职位列表1号']
    thread_spider = []
    for spidername in Spider_list:
        thread = lagou_spider(threadname = spidername,dataqueue=dataqueue,pagequeue=pagequeue,userqueue = userqueue,lock=lock,proxies=proxies)
        thread.start()
        thread_spider.append(thread)
   
    Parse_list = ['爬取职位详情1号','爬取职位详情2号']
    thread_parse = []
    for parsename in Parse_list:
        thread = lagou_parse(threadname = parsename,dataqueue = dataqueue,filename= filename,lock=lock2,proxies = proxies)
        thread.start()
        thread_parse.append(thread)

    #等待爬取职位列表完成再往下进行
    while not pagequeue.empty():
        pass
    print('pagequeue为空了')
    for thread1 in thread_spider:
        thread1.join()
        print('1')

    #等待爬取职位详情完成再往下进行
    while not dataqueue.empty():
        pass
    print(not dataqueue.empty())
    PARSE_EXIT = True
    print('所有职位列表爬取完毕')
    for thread in thread_parse:
        thread.join()
        print ("2")

    with lock2:
        # 关闭文件
        filename.close()
    print ("终于爬完了，谢谢使用！")

