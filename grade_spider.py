import requests
from bs4 import BeautifulSoup as bs 
import os
import random,time
import re
import pandas as pd
import sys

path = os.path.abspath(os.path.dirname(sys.argv[0]))#获得当前路径
outputpath = path+'\\output'#创建output文件夹用




base_url='http://us.nwpu.edu.cn/eams/login.action'#登录页面
def mkdir(path):#创建文件夹
    path =path.strip()#去空字符
    path = path.rstrip("\\")# 去除尾部 \ 符号
    isExists = os.path.exists(path)
    if not isExists: # 如果不存在则创建目录
        os.makedirs(path)
        return True
    else: # 如果目录存在则不创建
        return None


def login(s,username,password):
    #登录
    ua_list=[#ua池
        'Mozilla/5.0 (compatible; Baiduspider/2.0; +http://www.baidu.com/search/spider.html)',
        #百度
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.94 Safari/537.36',
        #谷歌   
        'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50', 
        # Safari   
        'Mozilla/4.0(compatible;MSIE7.0;WindowsNT5.1;Maxthon2.0)'
        #傲游（Maxthon）
    ]#随机选择一个ua
    ua = random.choice(ua_list)
    print("模拟浏览器，随机选择User-agent："+ua)
    # proxies_list = [#公网IP池
    #     {'http': '222.95.144.180:3000'},
       
    # ]#随机选择一个公网IP和端口
    # proxies = random.choice(proxies_list)
    # 首先获取到登录界面的html
    html = s.get(base_url,headers={'User-agent':ua})
    soup = bs(html.text, 'lxml')
    # 教务系统
    # 找到form的验证参数
    encodedPassword = soup.find('input', attrs={'name': 'encodedPassword'})['value']
    session_locale = soup.find('input', attrs={'name': 'session_locale'})['value']
  
    # 构造需要post的参数表
    FormData = { 
            'username':username,
            'password':password,
            'encodedPassword': encodedPassword,
            'session_locale':session_locale,
            }

    print('登录中……\n……\n')
# 测试看看是否能找到登陆后的信息 #获得用户信息
    post_login =s.post(base_url,data=FormData,headers={'User-agent':ua})
    html_login = post_login.text
    soup_login = bs(html_login, 'lxml')
    try:
        #是否登录成功，原来的页面没有登录或者登录失败时，有一个input标签，属性name值为username
        #如果能够找到name代表登录失败，如果没有，则成功
        name = soup_login.find('input',attrs={'name':'username'})
        if name==None:
        # print(soup_login)
            print('========成功登录西北工业大学教务系统========\n')
            return s
        else:#这步是学号和密码错误
            print( "登录失败,用户名或密码错误……")
    except:#异常重试
        print( "登录失败，请再试……")
               
    return None

def search_part(s,termID):#被search_grade调用
    #查找部分函数，返回查找结果
    #特定学期页的url地址
    term_url = 'http://us.nwpu.edu.cn/eams/teach/grade/course/person!search.action?semesterId='+str(termID)+'&projectType='
    html_grade =s.get(term_url).text
    soup_grade = bs(html_grade,'lxml')
    head_grade = soup_grade.find('thead',attrs={'class':"gridhead"})#找成绩单部分
    heads = head_grade.find_all('th')#找成绩单头部信息
    trs_dict={}
    num=0#作计数器
    for eachhead in heads:
        trs_dict[num]=[eachhead.text.strip()]#去空格
        num = num +1#num为index
    #num为列数
    #找到表示成绩的部分
    tbody = soup_grade.find('tbody')#attrs={'id':'grid16527563961_data'})
    #获得表格所有内容
    trs = tbody.find_all('tr')
    for eachtr in trs:#每一个tr 即每一门课
        tds=eachtr.find_all('td')#获得td的列表
        #放入字典中
        k = 0
        for eachtd in tds:
            trs_dict[k].append(eachtd.text.strip())
            k=k+1
        
    newtrs_dict={}
    #重新创建键不是索引1234等的字典，方便后续放入dataframe中
    for i in range(num):
        newtrs_dict[trs_dict[i][0]]=trs_dict[i][1:]
    gradetable = pd.DataFrame(newtrs_dict)#转化为dataframe
    print(gradetable)#打印
    return gradetable

def search_grade(s):
#查询成绩  学期表 存储跳转的url参数semsterid
    term_url_list = [
        ['2017-2018年秋学期',17],
        ['2017-2018年春学期',35],
        ['2018-2019年秋学期',18],
        ['2018-2019年春学期',36],
        ['2019-2020年秋学期',19],
        ['查询以上所有学期',0],
    ]
    print('目前可以查询的学期有————')
    
    for i in range(len(term_url_list)):#输出可以查找的范围
        print(str(i+1)+'、'+term_url_list[i][0])

    inputID = input("输入对应序号查询该学期的成绩：")
    try:
        inputID = int(inputID)
    except:
        print('参数错误！')
        return None
    print('\n查询'+term_url_list[inputID-1][0]+'成绩结果:\n')
    #成绩单的url以及url参数
    if inputID==6:
        mkdir(outputpath)#创建output文件夹
        writer = pd.ExcelWriter(outputpath+'\\所有学期成绩单.xlsx')#追加输出至同一个表格
        for i in range(1,6):
            print('sleep for 3 seconds---')
            time.sleep(3)#设置访问时间间隔
            termID=term_url_list[i-1][1]#获得学期的semid参数
            gradetable=search_part(s,termID=termID)#查找函数
            gradetable.to_excel(writer, str(term_url_list[i-1][0]))#输出
            writer.save()

    else:#单个学期的查找
        print('sleep for 3 seconds---')
        time.sleep(3)#设置访问时间间隔
        termID=term_url_list[inputID-1][1]
        gradetable=search_part(s,termID=termID)
        mkdir(outputpath)
        gradetable.to_excel(outputpath+'\\{}成绩单.xlsx'.format(term_url_list[inputID-1][0]),encoding='utf-8', index=True, header=True)
    
    print('\n=========成绩单以excel文件格式保存至output文件夹中=========\n')

if __name__ == "__main__":
    while(1):
        username=input("请输入学号/工号：")
        password = input("请输入密码：")
        s = requests.session()#设置session，页面跳转时不会退出
       
        s= login(s,username,password)#登录
        if s:#登录成功
            while(1):
                search_grade(s)#查找，调用search_part()
                cont = input('是否继续？(y or n) ')
                if cont=='y':
                    continue
                else:
                    break
            break
        else:#登录失败
            cont = input('是否继续？(y or n) ')
            if cont=='y':
                continue
            else:
                break
    print('===========END=============\n')
    