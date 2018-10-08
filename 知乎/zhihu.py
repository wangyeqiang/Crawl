from bs4 import BeautifulSoup
import requests

def zhuhuLogin():
	#构建一个Session对象，可以保存Cookie
	sess = requests.Session()
	#请求报头
	headers = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv2.0.1) Gecko/20100101 Firefox/4.0.1"}
	#首先获取登录界面，找到需要POST的数据(_xsrf),同时会记录当前网页cookie的值
	html = sess.get("http://www.zhuhu.com/#singnin",headers =headers).text
	#调用解析库
	bs = BeautifulSoup(html,"html.parser")

	#获取xsrf的值
	_xsrf = bs.find("input",attrs = {"name":"_xsrf"}).get("value")

	print(_xsrf)

zhuhuLogin()