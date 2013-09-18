#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
import os
#os.chdir("/root")

import sys
import time
import mimetools
import socket, thread, select
import pdb
import libs
import gzip



BUFSIZ=1024*8 # 8K

class BaseHTTP(object):
    # 从sock中读取一行
    def _ReadLine(self):
        end = -1
        cnt = 0
        while cnt<10:
            end=self.Buff.find("\r\n")
            if end!=-1:
                break
            tmp=self.sock.recv(BUFSIZ)
            if  not tmp:
                time.sleep(100)
                cnt+=1

            self.Buff+=tmp
        ret = self.Buff[:end]
        self.Buff=self.Buff[end+2:]
        return ret

    # 从sock中读取Size字节 到Body
    def _ReadBody(self,size):
        cnt = 0
        while size>len(self.Buff) and cnt <10:
            tmp=self.sock.recv(BUFSIZ)
            if  not tmp:
                time.sleep(100)
                cnt+=1
            self.Buff += tmp
        self.Body=self.Buff[:size]
        self.Buff=self.Buff[size:]

    def __init__(self,sock):
        self._ack = False
        self.sock=sock
        self.Body=""
        self.Buff=""
        # 请求行
        self.Line = self._ReadLine()
        # 请求头
        self.Headers={}
        while True:
            tmp=self._ReadLine()
            if not tmp:
                break
            v,k=tmp.split(":",1)
            if not self.Headers.has_key(v):
                self.Headers[v]=[]
            self.Headers[v].append(k.strip())
        # 请求体 长度
        self.Chunked = False
        self.BodyLength = 0
        self.SendLength = 0
        if self.Headers.has_key("Content-Length"):
            self.BodyLength=int(self.Headers["Content-Length"][0])
        if self.Headers.get("Transfer-Encoding",[""])[0]=="chunked":
            self.BodyLength = -1
            self.Chunked = True
        if self.Headers.get("Connection",[""])[0]=="close":
            while True:
                (r,_,_)=select.select([self.sock],[],[self.sock],10)
                tmp=""
                if len(r):
                    tmp=self.sock.recv(BUFSIZ)
                if tmp:
                    self.Buff+=tmp
                else:
                    break
            self.BodyLength=len(self.Buff)

    # 返回请求头的Str形式
    def _StrHeaders(self):
        str = ""
        for k in self.Headers.keys():
            for v in self.Headers[k]:
                str += k + ": " + v +'\r\n'
        return str

    # 默认片段处理函数 ，放行片段
    # 返回 True / False 是否放行
    def HeadleData(self):
        return True

    # 截取一段Body
    def GetData(self):
        if self.Chunked:
            #pdb.set_trace()
            tmp=self._ReadLine()
            ChunkLen=int(tmp,16) # 获得分片长度
        else:
            ChunkLen=min(BUFSIZ,self.BodyLength-self.SendLength)
        self._ReadBody(ChunkLen)
        if ChunkLen == 0:
            self.BodyLength = self.SendLength
        else:
            self.SendLength += len(self.Body)
        if self.Chunked:
            self._ReadLine()

    # 返回Body 字符串形式
    def StrBody(self):
        #pdb.set_trace()
        if self.Chunked:
            return hex(len(self.Body))[2:] + "\r\n" + self.Body + '\r\n'
        return self.Body

    # 返回是否已经结束
    def OddData(self):
        return self.BodyLength != self.SendLength

    # 是否 Keep-Alive
    def KeepConnection(self):
        return self.Headers.get("Connection",[""])[0].startswith("keep-alive") or self.Headers.get("Proxy-Connection",[""])[0].startswith("keep-alive")

    def Debug(self):
        print self.Line + " " + str(self.BodyLength)

class HTTPRequest(BaseHTTP):

    def __init__(self,client):
        super(HTTPRequest,self).__init__(client)
        self.Method,self.Path,self.Protocol=self.Line.split(" ",2)
        if self.Path.startswith("http://"):
            self.Path=self.Path[7:]
            st=self.Path.find("/")
            if st!=-1:
                self.Path=self.Path[st:]
            else:
                self.Path="/"

    def StrHeaders(self):
        return ' '.join([self.Method,self.Path,self.Protocol]) + '\r\n' + self._StrHeaders() + "\r\n "

#    def Debug(self):
#        print self.StrHeaders()

class HTTPResponse(BaseHTTP):
    def __init__(self,target):
        super(HTTPResponse,self).__init__(target)
        self.Protocol,self.Code,self.State=self.Line.split(" ",2)
    def StrHeaders(self):
        return ' '.join([self.Protocol,self.Code,self.State]) + '\r\n'  + self._StrHeaders()+ "\r\n"
#    def Debug(self):
#        print self.StrHeaders()

class BaseProxyHandler():
    def __init__(self, connection, address, timeout):
        self.client = connection
        self.address = address
        self.client.settimeout(timeout)
        self.client.setblocking(True)
        self.target = None
        self.timeout = timeout
        self.HostFunc = ""
        self.HandleHTTPRequestFunc = None
        self.HandleHTTPResponseFunc = None
        self.handle()

    def SockAlive(self):
        if self.target is None:
             return False
        (_,_,err)=select.select([],[],[self.client,self.target],0)
        return  len(err)==0

    def ConnectTarget(self):
        host = ""
        port = 80
        if self.Request.Headers.has_key("Host"):
            host = self.Request.Headers["Host"][0]
            if host.find(":")!=-1:
                host,port=host.split(":")
        else:
            self.KeepConnection = 0
        (soc_family, _, _, _, address) = socket.getaddrinfo(host,int(port))[0]
        self.target = socket.socket(soc_family)
        self.target.settimeout(self.timeout)
        self.target.setblocking(True)
        self.target.connect(address)

    def InitFunc(self):
        host=self.Request.Headers.get("Host")[0]
        if self.HostFunc != host:
            self.HostFunc = host
            self.HandleHTTPRequestFunc=libs.GetHandleHTTPRequestFunc(host)
            self.HandleHTTPResponseFunc=libs.GetHandleHTTPResponseFunc(host)
    def HandleHTTPRequest(self):
        self.Request._ack=True
        self.Request.Debug()
        for func in self.HandleHTTPRequestFunc:
            if callable(func):
                func(self)

    def HandleHTTPResponse(self):
        self.Response._ack=True
        self.Response.Debug()
        for func in self.HandleHTTPResponseFunc:
            if callable(func):
                func(self)
        pass

    def handle(self):
        self.KeepConnection = 1
        while self.KeepConnection:
    #        pdb.set_trace()
            # 生成Http请求
            try:
                self.Request=HTTPRequest(self.client)
                # 初始化处理函数列表
                self.InitFunc()
                # 修改Http请求
                self.HandleHTTPRequest()
                # 如果允许Http请求通过
                if self.Request._ack:
                    if self.target is None or not self.SockAlive():
                        self.ConnectTarget()
                    self.target.sendall(self.Request.StrHeaders())
                    while self.Request.OddData() and self.SockAlive():
                        self.Request.GetData()
                        if self.Request.HeadleData():
                            self.target.sendall(self.Request.StrBody())
                    self.Response=HTTPResponse(self.target)
                # 修改Http响应
                self.HandleHTTPResponse()
                # 如果允许Http响应通过
                if self.Response._ack:
                    self.client.sendall(self.Response.StrHeaders())
                    while self.Response.OddData() and self.SockAlive():
                        self.Response.GetData()
                        if self.Response.HeadleData():
                            self.client.sendall(self.Response.StrBody())
                self.KeepConnection=self.Response.KeepConnection() and self.Request.KeepConnection() and self.SockAlive()
                self.KeepConnection=0
            except Exception as err:
                #raise err
                print "!!! Error"
                self.KeepConnection=0
        self.client.close()
        self.target.close()


def StartProxy(host='0.0.0.0', port=8080, handler=BaseProxyHandler):
    timeout=5
    soc_type=socket.AF_INET
    soc = socket.socket(soc_type)
    soc.bind((host, port))
    print "Serving on %s:%d."%(host, port)#debug
    soc.listen(20)
    while True:
        connection, address = soc.accept()
        handler(connection,address,timeout)
    #while True:
    #    thread.start_new_thread(handler, soc.accept()+(timeout,))

def StartWebApp(host='0.0.0.0', port=8088, handler=libs.RootApp):
    handler.run(host=host,port=port)

if __name__ == '__main__':
    thread.start_new_thread(StartProxy,())
    StartWebApp()
    #StartProxy()
