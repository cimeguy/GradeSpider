# 西工大教务系统成绩爬虫-GraderSpider


高丽&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;2019.03完成
<!-- TOC -->

- [西工大教务系统成绩爬虫-GraderSpider](#西工大教务系统成绩爬虫-graderspider)
    - [一、实验目的](#一实验目的)
    - [二、系统设计思路](#二系统设计思路)
        - [（1）实现功能](#1实现功能)
        - [（2）框架思路](#2框架思路)
        - [（3）所需环境说明](#3所需环境说明)
    - [三、详细设计实现](#三详细设计实现)
        - [（1）登录](#1登录)
        - [（2）爬取](#2爬取)
        - [（3）应对反爬虫](#3应对反爬虫)
    - [四、实验结果及分析](#四实验结果及分析)
    - [五、源码地址](#五源码地址)

<!-- /TOC -->
## 一、实验目的
1. 掌握基本的爬虫，能够爬取特定的内容
2. 掌握模拟浏览器登录
3. 掌握GET、POST等请求方式
4. 了解反爬虫

## 二、系统设计思路
### （1）实现功能
1. 模拟登录教务系统      
2. 按用户需求爬取相应成绩
3. 一个简单的应对反爬虫的策略
   
### （2）框架思路
1. 首先爬取登录页面的表单中的其他信息，记录下来，输入学号、密码，提交所有表单信息，随机选择User-agent模拟浏览器登录；
2. 添加session，使得能够访问同一个网站的不同页面；
3. 代码本身通用，支持爬取所有学期，不过考虑到2017年入学，之前没有成绩，故只给出从“2017-2018秋”至今所有学期的选项，可以查看单个学期，也可以查看所有学期。输入选项，按需求爬取，保存至`output/***.xlsx`

### （3）所需环境说明
- 需要requests、bs4、(lxml)、pandas、(openpyxl)

- 注意，需将所有库都更新到最新，否则部分函数无法使用：
    ``` 
    pip list  # 查看已安装的所有的依赖包
    pip list --outdated -- format==columns  # 像表格一样列出所有已安装的依赖包的当前版本和可升级版本
    # 升级所有依赖包含如下两个命令
    pip install pip-review --user  # 先安装pip-review函数
    pip-review --local --interactive  # 成功升级所有的依赖包
    ```





## 三、详细设计实现
### （1）登录

- 问题a
  
    一开始决定从翱翔门户登录，再跳转至教务系统，进入成绩模块，但是发现怎么都无法登录成功。于是查询`Network`-`Headers`-`Form Data`发现：

    ![随机数](http://img.elfship.cn/img/QQ图片20200315002639.png)
    
    ![随机数放大](http://img.elfship.cn/img/QQ图片20200316114311.png)

    该处绿色箭头表示有一个随机数 `1t` 以及其他信息，随机数每次提交表单前就已经存在，并且每次提交完以后会变化。其他信息是固定值。

    同时，还发现学号和密码都是明文表示，也没有验证码和其他特殊信息。
    - 解决方法 
    
        应对策略是：先GET请求网页，将除了学号、密码以外的所有表单信息全部记录下来，接着连同学号和密码一起提交，即可登录。

- 问题b
        
    成功登录后还是遇到了另外一个问题：即使利用session也无法在翱翔门户跳转到教务系统。
        

    - 解决方法
  
        并没有找到具体原因。

        于是放弃从翱翔门户进入教务系统，而是直接找到教务系统的特定登录url: `http://us.nwpu.edu.cn/eams/login.action` 然后继续观察FormData，发现这次登录的表单信息更加简单，省略了随机数，仅有`username`、`password`、`encodedPassword`(这里为空)、`session_locale`（设置中英文的选项，中文用“zh-CN”表示）
        ![QQ图片20200316115059](http://img.elfship.cn/img/QQ图片20200316115059.png)
    
    最后顺利登录。
- 关于判断是否登录成功：
  
    原来的页面没有登录或者登录失败时，源码里有一个input标签，其属性name值为username,所以如果能够找到这个标签，则代表登录失败，如果没有，则代表已经跳转——登录成功。
    ![name](http://img.elfship.cn/img/QQ图片20200316122348.png)

    
### （2）爬取
成绩部分的url非常有规律，可以直接指定参数`semesterId`以访问不同学期的成绩单。例如访问`2019-2020秋学期`可以设置`semesterId`为`19`，其对应网址为`http://us.nwpu.edu.cn/eams/teach/grade/course/person!search.action?semesterId=19&projectType=`

- 问题  
  
    成绩部分的代码虽然并没有用js或其他机制，是可以直接爬取的，但还是遇到了问题——每个学期的成绩表格格式不一样，例如有的学期有实验成绩，而有的学期没有；
    ![成绩单格式](http://img.elfship.cn/img/QQ图片20200315004729.png)
    
    并且，经过测试发现，不同人在同一学期的表格也不一样，有的人有补考成绩，有的人没有。所以不能用简单的索引来读取。
    
    
    再加上，源码中这些选项之间在属性和标签上没有任何差异，无法通过BeautifulSoup的find函数读取特定的某一属性：
    ![QQ图片20200316115446](http://img.elfship.cn/img/QQ图片20200316115446.png)
    
    - 解决方法
    
        直接全部读取，然后利用pandas的DataFrame数据结构保存,可以实现项名和值之间的映射,非常方便。
        
        首先利用字典将“课程序号”“课程代码”“课程名称”等这些属性全部读取，接着逐行读取数据（每个`tr`属性代表一节课，每个`td`属性代表一项数值），最后转化为DataFrame格式。这样代码对于任何格式的表格都可以直接读取。

        并且pandas只需调用to_excel函数即可输入到xlsx文件。


### （3）应对反爬虫
实际上并没有发现教务系统的登录和成绩单有明显的反爬虫的机制（教务处的登录表单上没有随机数，复杂程度与翱翔门户比也差了很多，数据也没有被隐藏）。

此外，甚至也没有看到robots协议。

但是为了以防万一，还是写了一个常用的、比较简单的应对反爬虫的策略——python的默认User-agent会暴露自己爬虫的身份，所以这里构造UA池，每次随机选用百度、谷歌、safari、Maxthon浏览器中的一个User-agent访问，这样可以认为是一个小网络中多个用户同时访问一个页面，即不会被认为是爬虫。
``` python 
ua_list=[#ua池
    'Mozilla/5.0 (compatible; Baiduspider/2.0; +http://www.baidu.com/search/spider.html)',
    #百度
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.94 Safari/537.36',
    #谷歌 
    'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50', 
    # Safari  
    'Mozilla/4.0(compatible;MSIE7.0;WindowsNT5.1;Maxthon2.0)'
    #（Maxthon）
]
```
## 四、实验结果及分析

1. 登录：输入学号、密码，得到开始界面：
![结果-界面](http://img.elfship.cn/img/QQ图片20200315010419.png)
1. 选择想查看的特定学期或全部学期，这里选择`2017-2018秋学期`，输入`1`：
![结果-输出](http://img.elfship.cn/img/QQ图片20200315010739.png)
此外还可以选择继续`y`，输入其他选项查看；如果选择`n`结束循环。   
1. 在同级目录下会出现一个新的output文件夹，所有爬虫内容均以excel表格形式保存在这里：
![excel文件](http://img.elfship.cn/img/QQ图片20200315010958.png)
4. 查看其中一个excel文件：
![表格](http://img.elfship.cn/img/QQ图片20200315015157.png)
    和翱翔门户的成绩单完全符合。

5. 性能指标：
   - 定义性能指标：`爬虫结果的准确性`，为了验证，找了其他同学帮忙测试，均未出错。在该指标上表现优异。
   - 此外，由于数据量并不大，并且输出发现时间上并无明显差异，故不考虑`时间`指标。

## 五、源码地址
https://github.com/cimeguy/GradeSpider

