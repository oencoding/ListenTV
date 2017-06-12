#!/usr/bin/python
# -*- coding: utf-8 -*-

import warnings
warnings.filterwarnings("ignore")
import os
import urllib2
from time import sleep
import m3u8
import multiprocessing
from Utility.TimeTools import *
import hashlib
from dejavu import Dejavu
from Models import Config
from functools import partial
from Utility.Download import request
import json

config= {
    "database": {
        "host": "192.168.69.165",
        "user": "root",
        "passwd": "root",
        "db": "dejavu2"
    }
}



def getFileMD5(file_fullpath):
    result = ""
    with open(file_fullpath, 'rb') as f:
        md5obj = hashlib.md5()
        md5obj.update(f.read())
        result = md5obj.hexdigest()
    return result


def download_to_file(fileurl, filefull_path, overwrite=False):
    if overwrite and os.path.exists(filefull_path):
        return
    try:
        f = urllib2.urlopen(fileurl)
        data = f.read()
        with open(filefull_path, "wb") as code:
            code.write(data)
    except Exception, e:
        pass


def save(fileurl, filefull_path, overwrite=False):
    # print(u'开始保存：', fileurl)
    img = request.get(fileurl, 3)
    f = open(filefull_path, 'wb')
    f.write(img.content)
    f.close()

def showProcessInfo(processInfo):

    info = json.dumps(processInfo,encoding='UTF-8',ensure_ascii=False)
    print getCURRENT_TSTime(),info

def download():
    processInfo = multiprocessing.Manager().dict()
    def downts_thread(url=None,save_dir=None,processInfo=None):

        # 获取频道名称
        channel_name = url.split('/')[-2]
        listfile_name = url.split('/')[-1]

        # 初始化提取信息
        processInfo = {channel_name: {'latest': '', 'action': '正在初始化', 'info': '正在初始化'}}
        showProcessInfo(processInfo)

        # 新建文件夹
        save_dir = os.path.join(save_dir, channel_name)
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        # list_file_name
        list_file_name = channel_name + "_" + listfile_name

        # list_file_full_path
        list_file_full_path = os.path.join(save_dir, list_file_name)
        pre_md5 = ""  # 文件校验码
        while 1:
            djv = Dejavu(config)
            # 保存ts流列表文件（cctv15_01.m3u8）
            processInfo[channel_name]['action'] = 'downloading'
            processInfo[channel_name]['info'] = 'downloading file:' + list_file_name
            showProcessInfo(processInfo)
            # save(url,list_file_full_path,True)
            download_to_file(url,list_file_full_path,True)
            #并计算校验码
            current_md5 = getFileMD5(list_file_full_path)  # 当前文件校验码

            # 对比是否有变化
            if current_md5==pre_md5:
                processInfo[channel_name]['action'] = 'thread sleeping'
                processInfo[channel_name]['info'] = 'there is no new media ,'+ channel_name+'-thread is sleeping'
                showProcessInfo(processInfo)
                #休息一下继续开始
                sleep(Config.TS_SLEEP);
                continue
            # 提取文件列表
            m3u8_obj = m3u8.load(url)
            # 间隔时间
            gap_time = m3u8_obj.target_duration

            base_URL = url[:url.rfind('/')+1]
            for index,file in enumerate(m3u8_obj.files):
                # 文件的网络路径
                file_url = base_URL + file
                # 获取开始时间
                ts_start_time = getTS_Format_Time(m3u8_obj.program_date_time, int(index * int(gap_time)))

                # 得到完整文件名
                file_temp_name = channel_name+"_"+ts_start_time+'.ts'
                file_full_path = os.path.join(save_dir,file_temp_name)


                song_name = os.path.splitext(os.path.basename(file_temp_name))[0]
                if not djv.isSongFingerPrinted(song_name):

                    #下载该文件
                    processInfo[channel_name]['action'] = 'downloading'
                    processInfo[channel_name]['info'] = 'downloading file:' + file_temp_name
                    showProcessInfo(processInfo)
                    download_to_file(file_url,file_full_path,False)

                    # 调用指纹提取程序提取指纹
                    processInfo[channel_name]['action'] = 'fingerprinting'
                    processInfo[channel_name]['info'] = 'fingerpinting file:' + file_temp_name
                    showProcessInfo(processInfo)
                    djv.fingerprint_file(file_full_path)
                else:
                    processInfo[channel_name]['action'] = 'skip fingerprinted'
                    processInfo[channel_name]['info'] = file_temp_name + 'has fingerprinted'
                    showProcessInfo(processInfo)

                # 更新信息
                processInfo[channel_name]['action'] = 'update-info'
                processInfo[channel_name]['info'] = channel_name+' has updated to ' + ts_start_time
                processInfo[channel_name]['latest'] = ts_start_time
                showProcessInfo(processInfo)
                # 清理文件
                processInfo[channel_name]['action'] = 'delete ts file'
                processInfo[channel_name]['info'] = 'deleting file:' + file_temp_name
                showProcessInfo(processInfo)
                if os.path.exists(file_full_path):
                    os.remove(file_full_path)

                # 提取完成更新文件校验码
                pre_md5 = current_md5
                # 是否需要清理历史数据

            # 休息一下继续开始
            processInfo[channel_name]['action'] = 'thread sleeping'
            processInfo[channel_name]['info'] = 'playlist has been stored,' + channel_name + '-thread is sleeping'
            showProcessInfo(processInfo)
            if os.path.exists(list_file_full_path):
                os.remove(list_file_full_path)
            sleep(Config.TS_SLEEP)


    urls = Config.TS_URLS
    save_dir = Config.TS_SAVE_PATH
    # thread_num = len(urls)
    thread_num = 1

    pids = []
    for i in range(thread_num):
        p = multiprocessing.Process(target=downts_thread, args=(urls[i],save_dir,processInfo,))
        p.start()
        pids.append(p)
    # 检查进程是否完成工作
    while 1:
        flag = True
        # print  processInfo
        for p in pids:
            if p.is_alive():
                flag = False
                break
        if flag:
            break
        sleep(1)



if __name__ == "__main__":
    pass
    download()





