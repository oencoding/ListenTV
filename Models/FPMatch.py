#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
import multiprocessing
from FPUnities import *
import copy
import redis

import Config

import FPSearch
import FPUnities
import os
import sys

import matplotlib.pyplot as plt
import numpy as np


def get_objfp_index(obj_fplist, fp_list):
    fp_index = {}
    for index, key in enumerate(fp_list):
        fp_index[key] = index
    return fp_index


def pick_itemcode(obj_fplist):
    result = {}
    for fp, data in obj_fplist.items():
        for item_code,positions in data.items():
            result[item_code]=1
    return result

def plot_search_result(obj_fplist,fp_list, inference_result, pic_title):
    # print 'search_obj:',obj_fplist
    xys = {}
    fpxy = {'x': [], 'y': []}
    for index,fp in enumerate(fp_list):
        current_time = index * Config.FP_GAP_TIME
        fpxy['x'].append(current_time)
        fpxy['y'].append(current_time)
        if not obj_fplist.has_key(fp):
            continue
        for item_code, positions in  obj_fplist[fp].items():
            #不在匹配结果中的节目去除
            if not inference_result.has_key(item_code):
                continue

            if not xys.has_key(item_code):
                xys[item_code] = {'x':[],'y':[]}
            # {'hauxin': [320900, 321000, 320900, 321000],'guanghuisuiyue': [320900, 321000, 320900, 321000],'jiazoulvguan': [320900, 321000, 320900, 321000]}
            for position in positions:
                xys[item_code]['x'].append(current_time)
                xys[item_code]['y'].append(position)


    fig = plt.figure()
    for index,key in enumerate(xys.keys()):
        X = np.array(xys[key]['x'])
        Y = np.array(xys[key]['y'])
        ax1 = fig.add_subplot(1, len(xys.keys()), index+1)
        # 设置标题
        if pic_title==None:
            ax1.set_title("%s(%s)" % (key,inference_result[key]['match_rate']))
        else:
            ax1.set_title("%s(%s)" % (pic_title,inference_result[key]['match_rate']))
        # 设置X轴标签
        # plt.xlabel(key)
        # 设置Y轴标签
        # plt.ylabel('Y')
        # 画散点图
        ax1.scatter(X, Y, c='g', marker='x')
        ax1.scatter(fpxy['x'], fpxy['y'], c='r', marker='.')
        ax1.set_xticks([])
        ax1.set_yticks([])
        # 设置图标
        # plt.legend(['search_result', 'test'])
    # 显示所画的图
    plt.show()

def fp_match(obj_fplist,fp_list):

    match_info = {}  # 用于记录每首音乐的命中次数即每首歌距离相同的最大是数目和其他信息 如 match_time['MAIDOU'] = 12
    dvalues = {} # 记录每个指纹的差值
    samedis_values = {} # 记录相同距离的数目
    obj_dis = {} # 记录目标距离，用于计算匹配次数

    #初始化
    item_code_list = pick_itemcode(obj_fplist).keys()
    for item_code in item_code_list:
        match_info[item_code] = {'match_times':0, 'match_rate':0, 'start_pos':-1, 'end_pos':-1}
        dvalues[item_code]={}
        samedis_values[item_code] = 0
        obj_dis[item_code]={'dis':0,'times':0}

    current_time = 0
    half_gap = Config.FP_GAP_TIME //2

    #统计距离次数
    for index,fp in enumerate(fp_list):
        current_time = index * Config.FP_GAP_TIME
        if not obj_fplist.has_key(fp):
            continue
        for item_code, positions in obj_fplist[fp].items():
            for postion in positions:
                dis = postion - current_time
                if dvalues[item_code].has_key(dis):
                    dvalues[item_code][dis]+= 1
                else:
                    dvalues[item_code][dis] = 1
    # print dvalues

    #统计目标距离
    for item_code, data in dvalues.items():
        for dis, times in data.items():
            if times > obj_dis[item_code]['times']:
                obj_dis[item_code]['dis'] = dis
                obj_dis[item_code]['times'] = times

    # print obj_dis

    #统计相同距离总和
    for item_code, distances in dvalues.items():
        for dis,times in distances.items():
            if times < Config.SAMEDIS_THREADHOLD:
                continue
            samedis_values[item_code] += times

    #统计覆盖次数
    for index, fp in enumerate(fp_list):
        current_time = index * Config.FP_GAP_TIME
        if not obj_fplist.has_key(fp):
            continue
        for item_code, positions in obj_fplist[fp].items():
            for postion in positions:
                dis = postion - current_time
                if dis == obj_dis[item_code]['dis']:
                    match_info[item_code]['match_times'] += 1
                    match_info[item_code]['start_pos'] = postion - current_time
                    match_info[item_code]['end_pos'] = postion + (len(fp_list)-index)*Config.FP_GAP_TIME
                    break
    # print 'obj_fplist:',obj_fplist
    for item_code,sametimes in samedis_values.items():
        match_info[item_code]['samedis'] = sametimes

    #统计覆盖率
    fp_len = len(fp_list)
    for item_code,data in match_info.items():
        match_info[item_code]['match_rate'] = float("%0.3f" % (1.0 * data['match_times'] / fp_len))

    return match_info

def inference(match_info,accurency_threadhold=Config.ACCURENCY_THREADHOLD):
    result = {}
    for item_code,match_data in match_info.items():
        if match_data['match_rate'] < accurency_threadhold:
            continue
        result[item_code] = match_data
    return result


def fp_match_maintest():
    import fp_library

    # filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/test/guanghuisuiyue1.mp3')
    # filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/test/guanghui-rec-00-05.mp3')
    # filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/test/guanghuisuiyue-louder1.mp3')
    # filename = os.path.join(os.path.dirname(os.path.abspath(__file__)),'../data/test/turandeziwo_high1_10-25.mp3')
    # filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/test/guanghuisuiyue_high1_91-96.mp3')
    # filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/test/guanghuisuiyue_high2_30-40.mp3')
    # filename = os.path.join(os.path.dirname(os.path.abspath(__file__)),'../data/music/hongyanjiu.mp3')
    # filename = os.path.join(os.path.dirname(os.path.abspath(__file__)),'../data/music/guanghuisuiyue.mp3')



    # filename = os.path.join(os.path.dirname(os.path.abspath(__file__)),'../data/wenhan/74956693_t4.mp4')
    # filename = os.path.join(os.path.dirname(os.path.abspath(__file__)),'../data/wenhan/74956693_t1.mp4')

    filename = os.path.join(os.path.dirname(os.path.abspath(__file__)),'../data/music_ip_rec_test/guanghuisuiyue_ip_rec_02.wav')


    print 'fp extracting....',
    pre = int(time.time() * 1000)
    fp_list = fp_extract(filename)
    # fp_list = fp_library.guanghuisame[:12]
    print 'fp_len',len(fp_list),
    curr_time = int(time.time() * 1000)
    print 'consume time is:',(curr_time - pre)
    pre = curr_time



    print 'searching fps...',
    obj_fplist = FPSearch.fp_synsearch_mul(fp_list)
    print 'search result len:',len(obj_fplist),
    curr_time =int(time.time() * 1000)
    print 'consume time is:', (curr_time - pre),str(int(len(fp_list)*1000.0 / (curr_time - pre)))+'/s'
    pre = curr_time



    print 'calculating match info...',
    match_info = fp_match(obj_fplist,fp_list)
    curr_time = int(time.time() * 1000)
    print 'consume time is:', (curr_time - pre)
    pre = curr_time
    # print match_info

    print 'inferencing...',
    inference_result = inference(match_info, Config.ACCURENCY_THREADHOLD)
    curr_time = int(time.time() * 1000)
    print 'consume time is: ', (curr_time - pre)
    pre = curr_time
    print 'inference reuslt:',len(inference_result),inference_result


    print 'ploting result...'
    plot_search_result(obj_fplist, fp_list, inference_result, None)
    print 'finished!'




def fp_matchrate_in_twovoice(voic1_filepath,voic2_filepath):

    def my_search_fp(file_path,item_code):
        fp_list = fp_extract(file_path)
        result = {}
        curr_time = 0
        for index, fp in enumerate(fp_list):
            curr_time = index*Config.FP_GAP_TIME
            if not result.has_key(fp):
                result[fp]={item_code:[curr_time]}
            elif not result[fp].has_key(item_code):
                result[fp][item_code]=[curr_time]
            else:
                result[fp][item_code] = result[fp][item_code] + [curr_time]
        return result

    file1_name = voic1_filepath.split('/')[-1].split('.')[0]
    file2_name = voic2_filepath.split('/')[-1].split('.')[0]

    print 'fp extracting....',
    pre = int(time.time() * 1000)
    fp_list = fp_extract(voic1_filepath)
    print 'fp_len',len(fp_list),
    curr_time = int(time.time() * 1000)
    print 'consume time is:',(curr_time - pre)
    pre = curr_time



    print 'searching fps...',
    obj_fplist = my_search_fp(voic2_filepath,file2_name)
    print 'search result len:',len(obj_fplist),
    curr_time =int(time.time() * 1000)
    print 'consume time is:', (curr_time - pre),str(int(len(fp_list)*1000.0 / (curr_time - pre)))+'/s'
    pre = curr_time



    print 'calculating match info...',
    match_info = fp_match(obj_fplist,fp_list)
    curr_time = int(time.time() * 1000)
    print 'consume time is:', (curr_time - pre)
    pre = curr_time
    # print match_info

    print 'inferencing...',
    inference_result = inference(match_info, 0.0)
    curr_time = int(time.time() * 1000)
    print 'consume time is: ', (curr_time - pre)
    pre = curr_time
    print 'inference reuslt:',len(inference_result),inference_result


    print 'ploting result...'
    plot_search_result(obj_fplist, fp_list, inference_result,file1_name+' and '+file2_name + '\'s similarity ')
    print 'finished!'

def fp_dis(fp1,fp2):
    result = int(fp1) ^ int(fp2)
    num = 0
    while(result):
        num += result & 0x01
        result >>= 1
    return num

def fp_matchlength_in_twovoice(source_filepath,rec_filepath):
    source_fplist = fp_extract(source_filepath)
    rec_fplist = fp_extract(rec_filepath)

    min_dis = sys.maxint;
    start_pos = -1;

    for start_index  in range(len(source_fplist)-len(rec_fplist)):
        curr_dis = 0;
        for i,rec_fp in enumerate(rec_fplist):
            sour_fp = source_fplist[start_index+i]
            curr_dis += fp_dis(sour_fp,rec_fp)
        if curr_dis < min_dis:
            min_dis = curr_dis
            start_pos = start_index
    return min_dis,start_pos

def find_mindis (rec_filepath,files_root):
    print rec_filepath.split('/')[-1].split('.')[0]+':'
    result_file = -1
    result_dis = sys.maxint
    result_pos = -1

    file_list = get_dir_files(files_root)
    for filename in file_list:
        print "\t"+filename.split('/')[-1].split('.')[0]+':',
        dis,pos = fp_matchlength_in_twovoice(filename,rec_filepath)
        print 'dis='+ str(dis)+", pos="+ str(pos)
        if dis < result_dis:
            result_file = filename.split('/')[-1].split('.')[0]
            result_dis = dis
            result_pos = pos

    print result_file, result_dis, result_pos


def test_matchrate():

    # filename1 = os.path.join(os.path.dirname(os.path.abspath(__file__)),'../data/test/guanghuisuiyue-louder1.mp3')
    # filename2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/music/guanghuisuiyue.mp3')

    # filename1 = os.path.join(os.path.dirname(os.path.abspath(__file__)),'../data/test/guanghuisuiyue_high1_91-96.mp3')
    # filename2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/music/guanghuisuiyue.mp3')

    # filename1 = os.path.join(os.path.dirname(os.path.abspath(__file__)),'../data/wenhan/74956693_t1.mp4')
    # filename2 = os.path.join(os.path.dirname(os.path.abspath(__file__)),'../data/wenhan/74956693_t9.mp4')


    # filename1 = os.path.join(os.path.dirname(os.path.abspath(__file__)),'../data/wenhan/74956693_t1.mp4')
    # filename2 = os.path.join(os.path.dirname(os.path.abspath(__file__)),'../data/wenhan/74977499_t1.mp4')

    # filename1 = os.path.join(os.path.dirname(os.path.abspath(__file__)),'../data/test/guanghuisuiyue_high2_30-40.mp3')
    # filename2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/music/guanghuisuiyue.mp3')


    filename1 = os.path.join(os.path.dirname(os.path.abspath(__file__)),'../data/test/guanghuisuiyue_rec_test1.mp3')
    filename2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/music/guanghuisuiyue.mp3')


    fp_matchrate_in_twovoice(filename1,filename2)

if __name__ == '__main__':

    # fp_match_maintest()
    # test_matchrate()
    filename1 = os.path.join(os.path.dirname(os.path.abspath(__file__)),'../data/test/turandeziwo2.mp3')
    # filename1 = os.path.join(os.path.dirname(os.path.abspath(__file__)),'../data/wenhan/source2_rm_rec_test/87121420_rm_rec_01.mp3')
    # file_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/wenhan/source2')
    file_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/music')
    find_mindis(filename1,file_root)
