#!/usr/bin/python
# -*- coding: utf-8 -*-

import time
import multiprocessing
from FPUnities import *
import copy
import redis

import Config
import itertools

def fp_vallist2objfplist(fp, var_list):
    result = []
    for var in var_list:
        result.append({fp:eval(var)})
    return result

def fp_str2dictlist(var_list):
    result = []
    for var in var_list:
        var = eval(var)
        result.append(var)
    return result

def fp_synsearch_qucik(fp_list,samefp):
    r1 = redis.Redis(host=Config.REDIS_SEARCH_DB_HOST, port=Config.REDIS_SEARCH_DB_PORT, db=Config.REDIS_SEARCH_DB_ID)
    result_obj_fplisttt = {}
    for fp in fp_list:
        temp = r1.smembers(fp)
        var_list = list(temp)
        dict_list = fp_str2dictlist(var_list)
        for dict_item in dict_list:
            if not samefp=='-1':
                fp = samefp
            if not result_obj_fplisttt.has_key(fp):
                result_obj_fplisttt[fp] = {dict_item['item_code']:[dict_item['pos']]}
            elif result_obj_fplisttt[fp].has_key(dict_item['item_code']):
                result_obj_fplisttt[fp][dict_item['item_code']].append(dict_item['pos'])
            else:
                result_obj_fplisttt[fp][dict_item['item_code']] = [dict_item['pos']]
    return result_obj_fplisttt

def fp_hanmingsearch(fp, dis):
    result = [fp]
    fp = "%032d" % int(str(bin(int(fp)))[2:])
    all_indexs = list(itertools.combinations(range(len(fp)), dis))
    for index in all_indexs:
        tem = list(fp)
        for pos in range(len(index)):
            tem[index[pos]] = '1' if tem[index[pos]] == '0' else '0'
        result.append(str(int(''.join(tem), 2)))
    return result

def fp_synsearch_mul(fp_list):

    # 多进程处理函数
    # {'4294722976': {'guanghuisuiyue': [124060, 124080]}}
    def subtread_search(fp_list, start,numner):

        r1 = redis.Redis(host=Config.REDIS_SEARCH_DB_HOST, port=Config.REDIS_SEARCH_DB_PORT,db=Config.REDIS_SEARCH_DB_ID)
        end=start+numner
        for fp in fp_list[start:end]:
            fp_tranformed = fp_hanmingsearch(fp,Config.DISTANS_TREADHOLD)
            batch_search_result = fp_synsearch_qucik(fp_tranformed, fp)
            if batch_search_result.has_key(fp):
                result_obj_fplist[fp] = batch_search_result[fp]

    def sub_thread_quick_search(fp_list, start, number, result_obj_fplist):
        end = start + number
        if end > len(fp_list):
            end = len(fp_list)
        fp_list = fp_list[start:end]
        batch_search_result = fp_synsearch_qucik(fp_list,'-1')
        for fp,data in batch_search_result.items():
            result_obj_fplist[fp] = data

    #去除重复的key和静音key
    temp_dict = {}
    for fp  in fp_list:
        if fp == '0':
            continue
        temp_dict[fp]=fp
    fp_list = temp_dict.keys()

    print 'fp cleaned len',len(fp_list),


    thread_num = multiprocessing.cpu_count()
    result_obj_fplist = multiprocessing.Manager().dict()
    pids = []

    #需要比较汉明距离的多进程
    if Config.DISTANS_TREADHOLD != 0:
        unit_num = len(fp_list) // thread_num
        for i in range(thread_num):
            number = unit_num
            if (i + 1) == thread_num:
                number = len(fp_list) - unit_num * i
            p = multiprocessing.Process(target=subtread_search, args=(fp_list, i * unit_num, number,))
            p.start()
            pids.append(p)
    else:
        unit_num = len(fp_list) // thread_num
        for i in range(thread_num):
            number = unit_num
            if (i + 1) == thread_num:
                number = len(fp_list) - unit_num * i
            p = multiprocessing.Process(target =  sub_thread_quick_search, args = (fp_list, i*unit_num, number, result_obj_fplist, ))
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
    return copy.deepcopy(result_obj_fplist) #转化为正常的dict

def get_time_stamp():
    return int(1000 * time.time())

def recognize_test():

    curr = 1000*time.time()
    pre = curr

    print 'start!'
    # fp_list = ['4294722976','2281699448','2281699568','2281699448','2281699568''2281699448','2281699568','2281699448','2281699568''2281699448','2281699568','2281699448','2281699568''2281699448','2281699568','2281699448','2281699568''2281699448','2281699568','2281699448','2281699568''2281699448','2281699568','2281699448','2281699568''2281699448','2281699568','2281699448','2281699568''2281699448','2281699568','2281699448','2281699568','2281699448','2281699568','2281699448','2281699568','2281699448','2281699568','2281699448','2281699568']
    fp_list = ['4294722976','2281699448','2281699568','2281699448','2281699568''2281699448','2281699568','2281699448','2281699568''2281699448','2281699568','2281699448','2281699568''2281699448','2281699568','2281699448','2281699568''2281699448','2281699568','2281699448','2281699568''2281699448','2281699568','2281699448','2281699568''2281699448','2281699568','2281699448','2281699568''2281699448','2281699568','2281699448','2281699568','2281699448','2281699568','2281699448','2281699568','2281699448','2281699568','2281699448','2281699568']
    obj_fplist = fp_synsearch_mul(fp_list)

    curr = 1000*time.time()
    print 'resume:',curr - pre
    print len(fp_list) / (curr - pre)*1000,'/s'
    pre = curr


    print obj_fplist
    # obj_fplist = fp_sort(obj_fplist)
    # print obj_fplist

def search_test():
    import fp_library
    fp_list = fp_library.huaxin1
    sum = 0
    for fp in fp_list:
        obj_fplist = fp_synsearch_mul([fp])
        for key in obj_fplist.keys():
            sum += len(obj_fplist[key])
    obj_fplist = fp_synsearch_mul(fp_list)

    sum1 = 0
    for key in obj_fplist.keys():
        sum1 += len(obj_fplist[key])
    print sum1,sum

if __name__ == '__main__':
    # redis_clean()
    # fp_test()
    # recognize_test()
    # search_test()
    # print 522//5
    # print str(bin(int('7')))[2:]
    print fp_synsearch_mul(['4294042654'])

    pass