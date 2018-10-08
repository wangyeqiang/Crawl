from bs4 import BeautifulSoup
import requests
from pytesseract import *
from PIL import Image
import time

def  captcha(captcha_data):
	with open("captcha.jpg","wb") as f:
		f.write(captcha_data)
	time.sleep(1)
	image = Image.open("captcha.jpg")
	text = image_to_string(image)

	print("机器识别后的验证码为" + text )
	command = input("输入Y表示验证正确，同意使用（输入其他键，表示自行输入）")
	if (command == "Y" or command =="y"):
		return text
	else:
		return input("请输入验证码：")










def zhuhuLogin():
	#构建一个Session对象，可以保存Cookie
	sess = requests.Session()
	#请求报头
	headers = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv2.0.1) Gecko/20100101 Firefox/4.0.1"}
	#首先获取登录界面，找到需要POST的数据(_xsrf),同时会记录当前网页cookie的值
	data = {
		"email":"1152611857@qq.com"
		"password":"1231231"
		captcha:text
	}


	html = sess.get("http://www.zhuhu.com/#singnin",headers =headers).text
	#调用解析库
	bs = BeautifulSoup(html,"html.parser")

	#获取xsrf的值,这个现在xsrf知乎没有了，所以好像也不太好使了
	_xsrf = bs.find("input",attrs = {"name":"_xsrf"}).get("value")

	# 根据UNIX时间戳，匹配出验证码的URL地址
    captcha_url = "https://www.zhihu.com/captcha.gif?r=%d&type=login" % (time.time() * 1000)
    # 发送图片的请求，获取图片数据流，
    captcha_data = sess.get(captcha_url, headers = headers).content
    # 获取验证码里的文字，需要手动输入
    captcha(captcha_data)

	

zhuhuLogin()