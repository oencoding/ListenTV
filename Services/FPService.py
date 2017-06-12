#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import os
import warnings
warnings.filterwarnings("ignore")
from dejavu import Dejavu
from dejavu.recognize import FileRecognizer

#指纹入库服务（单曲单进程，多曲多进程）
def fplist_save_service():
    pass


#指纹提取服务
def get_fplist_service():
    pass

#指纹搜索服务
def search_fp_service():
    pass

#指纹匹配服务
def match_fp_service(filename):


    from Models.FPMatch import *
    # 参数检查
    if not os.path.isabs(filename):
        print '文件应为绝对路径'
        raise
    if not os.path.exists(filename):
        print '文件不存在'
        raise


    print 'fp extracting....'
    pre = int(time.time() * 1000)
    fp_list = fp_extract(filename)
    curr_time = int(time.time() * 1000)
    print 'consume time is:', (curr_time - pre)
    pre = curr_time
    print 'fp_len', len(fp_list)

    print 'searching fps...'
    obj_fplist = FPSearch.fp_synsearch_mul(fp_list)
    curr_time = int(time.time() * 1000)
    print 'consume time is:', (curr_time - pre)
    pre = curr_time
    print 'search result len:', len(obj_fplist)


    print 'calculating match info...'
    match_info = fp_match(obj_fplist, fp_list)
    curr_time = int(time.time() * 1000)
    print 'consume time is:', (curr_time - pre)
    pre = curr_time

    print 'inferencing...'
    inference_result = inference(match_info)
    curr_time = int(time.time() * 1000)
    print 'consume time is: ', (curr_time - pre)
    pre = curr_time
    print 'inference reuslt:', inference_result

    return inference_result
def dejavu_match_service(file_path):

    config= {
        "database": {
            "host": "127.0.0.1",
            "user": "root",
            "passwd": "root",
            "db": "dejavu2"
        }
    }

    djv = Dejavu(config)
    song = djv.recognize(FileRecognizer, file_path)
    result = {}
    if song != None:
    # {'guanghuisuiyue': {'end_pos': 96160, 'match_rate': 0.804, 'match_times': 181, 'start_pos': 91660, 'samedis': 820}}
    # {'song_id': 1, 'song_name': 'guanghuisuiyue', 'file_sha1': '3349023A0823907E12DC7CD76A20817C5DF977A8', 'confidence': 186, 'offset_seconds': 0.04644, 'match_time': 0.5880670547485352, 'offset': 1}
        result={song['song_name']:{'end_pos': -1, 'match_rate': -1, 'match_times': -1, 'start_pos': int ("%d" % song['offset_seconds']), 'samedis': -1}}

    print file_path.split('/')[-1]+":",song
    return result
