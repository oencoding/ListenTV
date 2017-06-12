#!/usr/bin/python
# -*- coding: UTF-8 -*-
import warnings
import json
import os
warnings.filterwarnings("ignore")

from Models.Tools import *

from dejavu import Dejavu
from dejavu.recognize import FileRecognizer

config= {
    "database": {
        "host": "127.0.0.1",
        "user": "root",
        "passwd": "root",
        "db": "dejavu2"
    }
}
def find_lcsubstr(s1, s2):
    m=[[0 for i in range(len(s2)+1)]  for j in range(len(s1)+1)]  #生成0矩阵，为方便后续计算，比字符串长度多了一列
    mmax=0   #最长匹配的长度
    p=0  #最长匹配对应在s1中的最后一位
    for i in range(len(s1)):
        for j in range(len(s2)):
            if s1[i]==s2[j]:
                m[i+1][j+1]=m[i][j]+1
                if m[i+1][j+1]>mmax:
                    mmax=m[i+1][j+1]
                    p=i+1
    return s1[p-mmax:p],mmax   #返回最长子串及其长度
def fingerprint_op(files_root,extensions):
    djv = Dejavu(config)
    djv.fingerprint_directory(files_root, extensions,nprocesses=1)

def audio_test(test_files_root=None,extensions=None):
    djv = Dejavu(config)

    file_list = get_dir_files(test_files_root,extensions)
    true_num = 0
    offsets = []

    statistics_off= {}
    avg_offsets = 0.0
    for index,filename in enumerate(file_list):

        music_name = filename.split('/')[-1].split('.')[0]
        song = djv.recognize(FileRecognizer, test_files_root+"/"+filename.split('/')[-1])
        flag = 'False'
        pos = 'False'
        if not song:
            continue

        if find_lcsubstr(song['song_name'],music_name)[1] >=2:
            true_num += 1
            flag = 'True'

        music_start_pos = float(music_name.split('_')[-2])
        result_pos = song['song_name'].split('_')[-2]
        tempos = float(result_pos) + float(song['offset_seconds'])
        offset = tempos-music_start_pos
        offsets.append(offset)

        if statistics_off.has_key(str(int(offset))):
            statistics_off[str(int(offset))] +=1
        else:
            statistics_off[str(int(offset))] =1


        print "%03d: %3d/%-3d %s offset:%02.3f  %-30s search_result:%-20s detail_info:%s" % ((index+1),true_num,len(file_list),flag,offset,music_name,song['song_name'],song)



    max_key = '0'
    max_value = -1
    for key,value in statistics_off.items():
        if int(statistics_off[key])> int(max_value):
            max_value = value
            max_key = key
    sum_pos = 0

    for off in offsets:
        if abs(int(off) - int(max_key)) <=1:
            sum_pos+=1
    print "%d/%-3d pos_true_num:%d" % (true_num,len(file_list),sum_pos)

    #16.5小时节目 + 100首歌曲 , 指纹16161748,分割成曲目6136首
if __name__ == '__main__':
    pass

    # files_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/internet/samples60')
    files_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/songs')
    fingerprint_op(files_root,['mp3'])

    # files_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/wanglei/TV10/specialfocus_2016_08_06')
    # fingerprint_op(files_root,['wav'])
    #
    # files_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/wanglei/TV10/diangetop_2016_01_17')
    # fingerprint_op(files_root,['wav'])



    # test_files_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/internet/cut_5s')
    # test_files_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/temp')
    # test_files_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/wanglei/TEST/daingetop')
    # test_files_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/wanglei/TEST/tiantianxiangshang20160212')
    # test_files_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/wanglei/TEST/aaaaa')
    # audio_test(test_files_root=test_files_root,extensions=['wav','mp3'])



