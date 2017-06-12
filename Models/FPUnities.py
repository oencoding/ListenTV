#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import redis

import Config
import multiprocessing
import math
from Models.Tools import *
def fp_extract(inputfile):

    #参数检查
    if not os.path.isabs(inputfile):
        print '文件应为绝对路径'
        return
    if not os.path.exists(inputfile):
        print '文件不存在'
        return

    ##执行命令生成指纹文件
    fp_result_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),"../data/temp/"+random_str(20)+'temp.afp')
    fp_log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),"../data/temp/"+random_str(20)+'temp.log')
    create_fp_cmd=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'openfp_extract %s %s > %s' % (inputfile,fp_result_file, fp_log_file))
    os.system(create_fp_cmd)

    ##读取指纹文件处理成列表
    result_list=[]
    fileobj = open(fp_result_file)
    list_lines = fileobj.readlines()

    for line in list_lines:
        line = line.split()[1]
        #去除静音key
        if line == '0':
            continue
        result_list.append(line)
    os.remove(fp_result_file)
    os.remove(fp_log_file)
    return result_list

def fp_process(fp_list, gap_time, item_code, offset_time, start_timestamp):
    point_offtime = offset_time
    point_timestamp = start_timestamp
    obj_fplist = []
    for fp in fp_list:
        val = {}
        val['item_code'] = item_code
        val['pos'] = point_offtime
        val['timestamp'] = point_timestamp

        ele={}
        ele[fp] = val
        obj_fplist.append(ele)

        point_offtime += gap_time
        point_timestamp += gap_time
    return obj_fplist

def fp_save(obj_fplist):
    r1 = redis.Redis(host='127.0.0.1',port=6379,db=0)
    r2 = redis.Redis(host='127.0.0.1',port=6379,db=1)
    pip_search = r1.pipeline()
    pip_lib = r2.pipeline()
    for fpele in obj_fplist:
        fp = fpele.keys()[0]
        pip_search.sadd(fp,fpele[fp])
        pip_lib.sadd(fp,fpele[fp])

    pip_search.execute()
    pip_lib.execute()
    return 1

def fp_clean(timestamp):
    pass


def redis_clean():
    r1 = redis.Redis(host='127.0.0.1', port=6379, db=0)
    r2 = redis.Redis(host='127.0.0.1', port=6379, db=1)
    r1.flushdb()
    r2.flushdb()


def get_dir_files( path ):
    if not os.path.exists(path):
        print 'path not exit'
        return []
    file_list=[]
    for root, dirs, files in os.walk( path ):
        for fn in files:
            file_list.append(root + '/' + fn)
    return file_list


def fp_test():

    # redis_clean()

    files_root=os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/music')

    file_list = get_dir_files(files_root)
    code_list = []
    for filepath in file_list:
        code_list.append(filepath.split('/')[-1].split('.')[0])

    def create_fp(file_list, code_list, start, numner):
        end = start+numner
        if end > len(file_list):
            end = len(file_list)
        print start,end
        code_list = code_list[start:end]
        for index,file in enumerate(file_list[start:end]):
            print str(start+index)+":"+code_list[index],
            fp_list = fp_extract(os.path.join(os.path.dirname(os.path.abspath(__file__)), file))
            obj_fplist = fp_process(fp_list, Config.FP_GAP_TIME, code_list[index], 0, 0)
            print fp_save(obj_fplist)

    thread_num = multiprocessing.cpu_count()
    unit_num = len(file_list) // thread_num
    pids = []
    for i in range(thread_num):
        number = unit_num
        if (i+1) == thread_num:
            number = len(file_list) - unit_num * i
        p = multiprocessing.Process(target =  create_fp, args = (file_list, code_list, i*unit_num,number, ))
        p.start()
        pids.append(p)
    #检查进程是否完成工作
    while 1:
        flag = True
        for p in pids:
            if p.is_alive():
                flag = False
                break
        if flag:
            break
    print 'finished!'


def fp_rec_test():
    file_yuan = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/test/guanghui-yuan-00-05.mp3')
    file_rec = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/test/guanghui-rec-00-05.mp3')

    # fp_extract(file_yuan)
    fp_extract(file_rec)

    pass
def fp_bin(num):
    return "%032d" % int(str(bin(int(num))).split('0b')[-1])




if __name__ == '__main__':

    redis_clean()
    fp_test()
    # fp_rec_test()
    # fp_bin()
    pass