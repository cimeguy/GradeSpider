##AJAX
import requests
from bs4 import BeautifulSoup as bs 
import os
import random
import re
import pandas as pd
import sys

path = os.path.abspath(os.path.dirname(sys.argv[0]))#获得当前路径
outputpath = path+'\\output'

base_url='http://us.nwpu.edu.cn/eams/login.action'#登录页面
def mkdir(path):
    path =path.strip()
    # 去除尾部 \ 符号
    path = path.rstrip("\\")
    isExists = os.path.exists(path)
    if not isExists:
        # 如果不存在则创建目录
        # 创建目录操作函数
        os.makedirs(path)
        return True
    else:
        # 如果目录存在则不创建
        return None


def login(s,username,password):
    #登录
    ua_list=[#ua池
        'Mozilla/5.0 (compatible; Baiduspider/2.0; +http://www.baidu.com/search/spider.html)',
        #百度
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.94 Safari/537.36',
        #谷歌    
        'Mozilla/4.0(compatible;MSIE7.0;WindowsNT5.1;Maxthon2.0)'
        #傲游（Maxthon）
    ]
    ua = random.choice(ua_list)#随机选择一个ua
    print("模拟浏览器，随机选择User-agent："+ua)

    #    首先获取到登录界面的html
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
        
        name = soup_login.find('input',attrs={'name':'username'})
        if name==None:
        # print(soup_login)
            print('========成功登录西北工业大学教务系统========\n')
            return s
        else:
            print( "登录失败,用户名或密码错误……")
    except:
        print( "登录失败，请再试……")
               
    return None

def search_part(s,termID):
    #查找完以后返回查找结果
    #特定学期页的url地址
    term_url = 'http://us.nwpu.edu.cn/eams/teach/grade/course/person!search.action?semesterId='+str(termID)+'&projectType='
    html_grade =s.get(term_url).text
    soup_grade = bs(html_grade,'lxml')
    head_grade = soup_grade.find('thead',attrs={'class':"gridhead"})
    heads = head_grade.find_all('th')
    trs_dict={}
    num=0
    for eachhead in heads:
        #num为index
        trs_dict[num]=[eachhead.text.strip()]#去空格
        num = num +1
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
    #重新创建不包含123index的字典，方便后续放入dataframe中
    for i in range(num):
        newtrs_dict[trs_dict[i][0]]=trs_dict[i][1:]

    gradetable = pd.DataFrame(newtrs_dict)#转化为dataframe
    print(gradetable)#打印
    return gradetable

def search_grade(s):
#查询成绩  学期表 存储跳转的url参数
    term_url_list = [
        ['2017-2018年秋学期',17],
        ['2017-2018年春学期',35],#这个学期没有实验成绩
        ['2018-2019年秋学期',18],
        ['2018-2019年春学期',36],
        ['2019-2020年秋学期',19],
        ['查询以上所有学期',0],
    ]

    print('目前可以查询的学期有————')
    #输出可以查找的范围
    for i in range(len(term_url_list)):
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
        mkdir(outputpath)
        writer = pd.ExcelWriter(outputpath+'\\所有学期成绩单.xlsx')
        for i in range(1,6):
            termID=term_url_list[i-1][1]
            gradetable=search_part(s,termID=termID)
            gradetable.to_excel(writer, str(term_url_list[i-1][0]))
            writer.save()

    else:

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
        s= login(s,username,password)
        if s:
            while(1):
                search_grade(s)
                cont = input('是否继续？(y or n) ')
                if cont=='y':
                    continue
                else:
                    break
            break
        else:
            cont = input('是否继续？(y or n) ')
            if cont=='y':
                continue
            else:
                break
    print('===========END=============\n')
    