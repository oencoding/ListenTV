#!/usr/bin/python
# -*- coding: UTF-8 -*-

import datetime
from pytz import timezone
from Models import Config
from datetime import timedelta
from Models import Config

def getCURRENT_TSTime():
    utc_now = datetime.datetime.utcnow()
    tzchina = timezone(Config.TS_ZONE)
    utc_now = utc_now.replace(tzinfo=timezone(Config.TS_ZONE)).astimezone(tzchina)
    return utc_now.strftime("%Y%m%d%H%M%S")


def getTS_Format_Time(datatime,offset):
    tzchina = timezone(Config.TS_ZONE)
    offset_time = timedelta(seconds=offset)
    real_time = datatime + offset_time
    real_time = real_time.replace(tzinfo=timezone(Config.TS_ZONE)).astimezone(tzchina)
    return real_time.strftime("%Y%m%d%H%M%S")


def pindaomingcheng():
    url = 'http://cn150.videocc.net/vod1/cctv14/01.m3u8'
    print url.split('/')[-2]

if __name__ == "__main__":
    pass
    utc_now = datetime.datetime.utcnow()
    print getCURRENT_TSTime()
    print getTS_Format_Time(utc_now,2)
