#!/usr/bin/python
# -*- coding: UTF-8 -*-
import errno
import os
import logging
import urllib2
import shutil
from Utility import crypto
from Utility import atomic
import urllib
import requests
import m3u8

def meu8test():
    tv_source = '/Users/simon/Documents/WORKSTATION/WorkSpaces/PyCharm/ListenTV/data/TVSource/examples/cctv15-01.m3u8'
    m3u8_obj = m3u8.load('http://cn150.videocc.net/vod1/cctv15/01.m3u8')

    print m3u8_obj.base_uri
    print m3u8_obj.files
    print m3u8_obj.target_duration


def download_ts():
    url = 'http://cn150.videocc.net/vod1/cctv15/01.m3u8'

    print "downloading with urllib2"
    f = urllib2.urlopen(url)
    data = f.read()
    with open("01.m3u8", "wb") as code:
        code.write(data)

    m3u8_obj = m3u8.load('01.m3u8')

    print m3u8_obj.base_uri
    print m3u8_obj.files
    print m3u8_obj.target_duration
    print m3u8_obj.program_date_time


    # item_id =



    for file in m3u8_obj.files:
        uri = m3u8_obj.base_uri+file
        print uri
        # download_to_file(uri,'../data/TSS');




if __name__ == '__main__':
    # hlstest()
    download_ts()
    pass

