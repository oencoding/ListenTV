#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import string
import random

def random_str(randomlength=8):
    a = list(string.ascii_letters)
    random.shuffle(a)
    return ''.join(a[:randomlength])
def extension_ok(ext,extensions=None):
    if extensions==None:
        return True
    ext = ext.lower()
    for tt in extensions:
        tt = str(tt).lower()
        if ext == tt:
            return True
    return False

def get_dir_files(path, extensions=None):
    if not os.path.exists(path):
        print 'path not exit'
        return []
    file_list=[]
    for root, dirs, files in os.walk( path ):
        for fn in files:
            ext = fn.split(".")[-1]
            if extension_ok(ext,extensions):
                file_list.append(root + '/' + fn)
    return file_list
def standart_and_seconds(info):
    flag = 1 # 00:01:11 ==>> 71
    info = str(info)
    if info.find(':') < 0:
        flag = 2
    result = -1
    if flag ==1:
        info = str(info)
        infos = info.split(":")
        result = int(infos[0])*3600 + int(infos[1])*60 + int(infos[2])
    else:
        info = int(info)
        hour = "%02d" % (info/3600)
        minits = "%02d" % (info%3600/60)
        seconds = "%02d" % (info%3600%60)
        result = hour + ':' + minits + ':' + seconds
    return result

if __name__ == '__main__':
    print standart_and_seconds(standart_and_seconds('124124312'))