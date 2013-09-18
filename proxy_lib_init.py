#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
import sys
import os
import bottle
import fnmatch

bottle.TEMPLATE_PATH.append("./libs/views/")
RootApp=bottle.Bottle()

RegLib=[]

@RootApp.route("/")
@bottle.view("index")
def index():
    return {"RegLib":RegLib}

HandleHTTPRequestFunc={}
HandleHTTPResponseFunc={}

def RegHandleHTTPRequestFunc(FuncList):
    for i in FuncList:
        host,func=i
        if not HandleHTTPRequestFunc.has_key(host):
            HandleHTTPRequestFunc[host]=[]
        if callable(func):
            HandleHTTPRequestFunc[host].append(func)

def RegHandleHTTPResponseFunc(FuncList):
    for i in FuncList:
        host,func=i
        if not HandleHTTPResponseFunc.has_key(host):
            HandleHTTPResponseFunc[host]=[]
        if callable(func):
            HandleHTTPResponseFunc[host].append(func)

def GetHandleHTTPRequestFunc(host):
    ret = []
    for i in HandleHTTPRequestFunc.keys():
        if fnmatch.fnmatch(host,i):
            ret.extend(HandleHTTPRequestFunc[i])
    return ret

def GetHandleHTTPResponseFunc(host):
    ret = []
    for i in HandleHTTPResponseFunc.keys():
        if fnmatch.fnmatch(host,i):
            ret.extend(HandleHTTPResponseFunc[i])
    return ret

def RegApp(path,app):
    RegLib.append(path)
    RootApp.mount(path,app)

def Init():
    sys.path.append("libs")
    for name in os.listdir("libs"):
        if name.endswith(".py") and name!="__init__.py":
            print "Loading "+name[:-3]
            __import__(name[:-3])

Init()
