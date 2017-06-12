#!/usr/bin/python
# -*- coding: utf-8 -*-

DISTANS_TREADHOLD=0 # 编码的汉明距离阈值

#btbu测试数据库
REDIS_SEARCH_DB_HOST='127.0.0.1' #redis 数据库位置
REDIS_SEARCH_DB_PORT='6379'#redis 数据库端口
REDIS_SEARCH_DB_ID='0' #redis 数据库名称

#文翰师兄测试数据库
SEARCH_AUDIO_DB_HOST='127.0.0.1' #redis 数据库位置
SEARCH_AUDIO_DB_PORT='6379'#redis 数据库端口
SEARCH_AUDIO_DB_ID='2' #redis 数据库名称


FP_GAP_TIME=20 #redis 指纹间隔时间 毫秒
SAMEDIS_THREADHOLD=5 #相同距离的个数的最小值，用于计算总的相同距离数目，降低过长的音频的权重
ACCURENCY_THREADHOLD=0.3#覆盖率（正确率）阈值
MATCH_DISERROR=0 #命中距离误差


TS_ZONE='UTC'
TS_SLEEP=5
TS_URLS=['http://cn150.videocc.net/vod1/cctv14/01.m3u8',
        'http://cn150.videocc.net/vod1/cctv13/01.m3u8',
        'http://cn150.videocc.net/vod1/cctv12/01.m3u8',
        'http://cn150.videocc.net/vod1/cctv15/01.m3u8'
        ]

#TS_URLS=['http://ver007.com/2016/07/25/706.html']
TS_SAVE_PATH='/home/zhangxinming/Desktop/TSData'
# TS_SAVE_PATH='/tmp/TSData'
