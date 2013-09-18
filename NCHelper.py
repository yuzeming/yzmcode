# -*- coding: utf-8 -*-
# 农场助手
# 请在背包内购买足够种子
# 修改QQ和PWD为自己的QQ号和密码
# 鱼塘部分暂时没有实现
import urllib2
import httplib
import cookielib
import HTMLParser
import BeautifulSoup
import urllib
import urlparse
import string
import re
import time
import datetime
import Queue

#修改此处
QQ = '909282837'
PWD =''


User_Agent = "Mozilla/5.0 (compatible; MSIE 9.0; Windows Phone OS 7.5; Trident/5.0; IEMobile/9.0; NOKIA; Lumia 800)"

SignInUrl = "http://ncapp.z.qq.com/nc/cgi-bin/wap_farm_index?all=1&g_ut=2&sid=%(sid)s&signin=1"
IndexUrl = "http://ncapp.z.qq.com/nc/cgi-bin/wap_farm_index?all=1&g_ut=2&sid=%(sid)s&B_UID=%(uid)s"
FriendListUrl = "http://ncapp.z.qq.com/nc/cgi-bin/wap_farm_friend_list_exp?g_ut=2&sid=%(sid)s&page=%(pg)d"
FarmOptUrl = "http://ncapp.z.qq.com/nc/cgi-bin/wap_farm_opt?g_ut=2&sid=%(sid)s&place=%(pid)d&act=%(act)s&B_UID=%(uid)s"
FarmStealUrl = "http://ncapp.z.qq.com/nc/cgi-bin/wap_farm_steal?sid=%(sid)s&g_ut=2&B_UID=%(uid)s&place=%(pid)d"
FarmHarvestUrl ="http://ncapp.z.qq.com/nc/cgi-bin/wap_farm_harvest?sid=%(sid)s&g_ut=2&place=%(pid)d"
FarmDigUrl = "http://ncapp.z.qq.com/nc/cgi-bin/wap_farm_dig?sid=%(sid)s&g_ut=2&place=%(pid)d&cropStatus=7"
FarmPlantUrl = "http://ncapp.z.qq.com/nc/cgi-bin/wap_farm_plant?sid=%(sid)s&g_ut=2&v=0&cid=%(cid)s&landid=%(pid)d"
FarmSeedListUrl = "http://ncapp.z.qq.com/nc/cgi-bin/wap_farm_seed_plant_list?sid=%(sid)s&g_ut=2&landid=%(pid)d&land_bitmap=0&page=%(pg)d"

#Fish
FishIndexUrl="http://ncapp.z.qq.com/nc/cgi-bin/wap_farm_fish_index?sid=%(sid)s&g_ut=2&&B_UID=%(uid)s"


def Get(url):
    """
    发送一个Get请求
    :param url:url to get
    :return:urlopen(req)
    """
    req = urllib2.Request(url)
    req.add_header("User-Agent",User_Agent)
    return urllib2.urlopen(req)

def Login(QQ,PWD):
    """
    登录QQ空间
    :param QQ:QQ号
    :param PWD: 密码
    :return: SID，失败（密码错误等）返回None
    """
    loginpage = Get("http://z.qq.com")
    pagesoup=BeautifulSoup.BeautifulSoup(loginpage.read())
    posturl=pagesoup.find(id="qq_loginform")["action"]
    data = {}
    hiddenvalue=pagesoup.find(id="qq_loginform").findAll(type="hidden")
    for tab in hiddenvalue:
        data[tab["name"]] = tab["value"]
    data["qq"] = QQ
    data["pwd"] = PWD
    req = urllib2.Request(posturl,urllib.urlencode(data))
    req.add_header("Origin","http://pt.3g.qq.com")
    req.add_header("Referer",loginpage.geturl())
    req.add_header("User-Agent",User_Agent)
    login = urllib2.urlopen(req)
    if BeautifulSoup.BeautifulSoup(login.read()).title.text == u"登录手机QQ空间":
        return None
    result=urlparse.urlparse(login.geturl())
    return urlparse.parse_qs(result.query)["sid"][0]

def FarmIndexParser(s):
    """
    解析农场状态网页
    :param s: HTML
    :return: a list
    [
        #[id"名称或None(空地)",成熟倒计时,可否播种,需要除草,需要杀虫,需要浇水,可以收获,需要铲除],
        [1,None,None,0,0,True,False,False,False,False,False],
        [2,"白萝卜","1:15",0,0,False,True,True,False,False],
        [3,"白萝卜",None,16,16,False,False,False,True,False],
    ]
    """
    p=re.compile(r"\d+")
    soup=BeautifulSoup.BeautifulSoup(s)
    List=soup.findAll("div",{'class':'module-content'})[2].findAll("div",{"class":"spacing-3 border-btm"})
    res=[]
    for item in List:
        #[id,"名称或None(空地)",成熟倒计时,可否播种,需要除草,需要杀虫,需要浇水,可以收获,需要铲除,可以偷取],
        tmp=[0,"",None,False,False,False,False,False,False,False]
        plist=item.findAll("p")
        name=plist[0].text.split()
        if len(name)<3:
            continue
        if name[1].startswith(u"("):
            name[2]=name[1]+name[2]
            del name[1]
        tmp[0]=int(p.findall(name[1])[0])-1
        if name[2].startswith(u"["):
            name[2]=name[2][0:name[2].find(u"]")+1]
        tmp[1]=name[2]
        if plist[1].span:
            s=plist[1].span.text
            if s.find(u"分后成熟")!=-1:
                a,b=p.findall(s)
                tmp[2]=int(a)*60+int(b)
        txt=[]
        for x in plist:
            txt.extend([i.text for i in x.findAll("a")])
        tmp[3]=bool(txt.count(u"播种"))
        tmp[4]=bool(txt.count(u"除草"))
        tmp[5]=bool(txt.count(u"杀虫"))
        tmp[6]=bool(txt.count(u"浇水"))
        tmp[7]=bool(txt.count(u"收获"))
        tmp[8]=bool(txt.count(u"铲除"))
        tmp[9]=bool(txt.count(u"摘取"))
        res.append(tmp)
    return res

def GetFarmIndex(sid,uid=0):
    html = Get(IndexUrl % {"sid":sid,"uid":uid} ).read()
    if html.find("你不在他的好友列表里。")>0:
        return None
    return FarmIndexParser(html)

def FishIndexParser(s):
    soup=BeautifulSoup.BeautifulSoup(s)
    List=soup.findAll("div","module-content")
    print List
    #TODO

def GetFishIndex(sid,uid=0):
    html = Get(FishIndexUrl %{"sid":sid,"uid":uid})
    if html.find("你不在他的好友列表里。")>0:
        return None
    return FishIndexParser(html)

def GetFriendList_(sid,pg):
    """
    返回某一页好友列表，并返回总页数
    :param sid:
    :param pg:
    :return:List,totpg
    """
    ret=[]
    html=Get(FriendListUrl % {"sid":sid,"pg":pg} ).read()
    soup=BeautifulSoup.BeautifulSoup(html)
    pageno=soup.find(text=re.compile(ur"第\d+/\d+页"))
    totpg=re.findall(r"\d+",pageno)[1]
    for a in  soup.findAll("div","module-content")[0].findAll("a",href=lambda x : x.startswith("./wap_farm_index")):
        url=urlparse.urlparse(a["href"])
        qs=urlparse.parse_qs(url.query)
        if qs.has_key("B_UID"):
            uid=urlparse.parse_qs(url.query)["B_UID"][0]
            ret.append(uid)
    return ret,int(totpg)

def GetFriendList(sid):
    """
    返回全部好友列表，B_UID
    :param sid:
    :return:
    """
    ret=[]
    ret,totpg=GetFriendList_(sid,1)
    for i in range(2,totpg+1):
        tmp,totpg=GetFriendList_(sid,i)
        ret.extend(tmp)
    return ret

def GetPlantID_(sid,pid,pg):
    """
    返回某一页种子列表，并返回总页数
    :param sid:
    :param pg:
    :return:List,totpg
    """
    ret=[]
    html=Get(FarmSeedListUrl % {"sid":sid,"pid":pid+1,"pg":pg} ).read()
    soup=BeautifulSoup.BeautifulSoup(html)
    pageno=soup.find(text=re.compile(ur"第\d+/\d+页"))
    totpg=re.findall(r"\d+",pageno)[1]
    for a in  soup.findAll("a",href=lambda x : x.find("wap_farm_plant")>=0):
        url=urlparse.urlparse(a["href"])
        qs=urlparse.parse_qs(url.query)
        if qs.has_key("cid"):
            cid=urlparse.parse_qs(url.query)["cid"][0]
            ret.append(cid)
    return ret,int(totpg)

def GetPlantID(sid,pid):
    """
    返回全部种子列表，B_UID
    :param sid:
    :return:
    """
    ret=[]
    ret,totpg=GetPlantID_(sid,pid,1)
    for i in range(2,totpg+1):
        tmp,totpg=GetFriendList_(sid,i)
        ret.extend(tmp)
    return ret

def FarmWork(sid,uid,fs):
    """
    在农场工作。返回下次访问农场的时间
    :param sid:sid
    :param uid:
    :param fs:
    :return 分钟,操作记录
    """
    ret=15
    info=[]
    for place in fs:
        #[id,"名称或None(空地)",成熟倒计时,可否播种,需要除草,需要杀虫,需要浇水,可以收获,需要铲除,可以偷取]
        if place[4]: #需要除草
            Get(FarmOptUrl % {"sid":sid,"uid":uid,"pid":place[0],"act":"clearWeed"})
            info.append(u"为%s的%d号土地除草"%(uid,place[0]))
        if place[5]: #需要杀虫
            Get(FarmOptUrl % {"sid":sid,"uid":uid,"pid":place[0],"act":"spraying"})
            info.append(u"为%s的%d号土地杀虫"%(uid,place[0]))
        if place[6]: #需要浇水
            Get(FarmOptUrl % {"sid":sid,"uid":uid,"pid":place[0],"act":"water"})
            info.append(u"为%s的%d号土地浇水"%(uid,place[0]))
        if place[7]: #可以收获
            Get(FarmHarvestUrl % {"sid":sid,"pid":place[0]})
            info.append(u"为%s的%d号土地收获%s"%(uid,place[0],place[1]))
            ret=0
        if place[8]: #需要铲除
            Get(FarmDigUrl % {"sid":sid,"pid":place[0]})
            info.append(u"为%s的%d号土地铲除"%(uid,place[0]))
            ret=0
        if place[9]: #可以偷取
            Get(FarmStealUrl % {"sid":sid,"uid":uid,"pid":place[0]})
            info.append(u"为%s的%d号土地偷取%s"%(uid,place[0],place[1]))
        if place[3]: #可否播种
            cid=GetPlantID(sid,place[0])
            if cid:
                Get(FarmPlantUrl % {"sid":sid,"pid":place[0]+1,"cid":cid[0]})
                info.append(u"为%s的%d号土地播种%s"%(sid,place[0],cid[0]))
        if place[2] and ret > place[2]:
            ret = place[2]
    return ret,info

def main():
    SID = Login(QQ,PWD)
    print u"登录成功%s" % (SID,)
    FL=GetFriendList(SID)
    #FL.append("0");
    print u'获取好友列表，共%d位好友' % (len(FL),)
    Q=Queue.PriorityQueue()
    for f in FL:
        Q.put([0,f])
    while not Q.empty():
        tmp=Q.get()
        if tmp[0]>time.time():
            print u"进入休息%d秒" % (tmp[0]-time.time(),)
            return 
            time.sleep(tmp[0]-time.time())
        print u"扫描%s的农场" %(tmp[1],)
        fs=GetFarmIndex(SID,tmp[1])
        print u"操作%s的农场" % (tmp[1],)
        tmp[0],info=FarmWork(SID,tmp[1],fs)
        for x in info:
            print x
        print u"%d分钟后再次访问%s的农场" % (tmp[0],tmp[1])
        tmp[0] = int(time.time()) + tmp[0]*60 + 10
        Q.put(tmp)

if __name__ == "__main__":
    main()
    #sid="AVY3Ed3CsoUr-fmQsk-UgK8n"
    #GetFishIndex(sid)
