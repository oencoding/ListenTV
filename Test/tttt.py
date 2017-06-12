from Models.SerachAudioUnities import *
import os
import re
from Models.FPUnities import fp_bin,fp_extract

def create_fp_file():
    files_root=os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/wenhan/source2')
    file_list = get_dir_files(files_root)
    for filename in file_list:
        fp_getfpfile(filename,filename.split('/')[-1].split('.')[0]+'.afp',False,True)

def create_fp_test():
    # filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/test/guanghuisuiyue1.mp3')
    filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/test/guanghui-rec-00-05.mp3')
    # filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/test/guanghuisuiyue-louder1.mp3')
    # filename = os.path.join(os.path.dirname(os.path.abspath(__file__)),'../data/test/turandeziwo_high1_10-25.mp3')
    # filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/test/guanghuisuiyue_high1_91-96.mp3')
    # filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/test/guanghuisuiyue_high2_30-40.mp3')
    # filename = os.path.join(os.path.dirname(os.path.abspath(__file__)),'../data/music/hongyanjiu.mp3')
    filename = os.path.join(os.path.dirname(os.path.abspath(__file__)),'../data/music/guanghuisuiyue.mp3')
    # filename = os.path.join(os.path.dirname(os.path.abspath(__file__)),'../data/music/turandeziwo.mp3')

    # filename = os.path.join(os.path.dirname(os.path.abspath(__file__)),'../data/wenhan/74956693_t4.mp4')
    # filename = os.path.join(os.path.dirname(os.path.abspath(__file__)),'../data/wenhan/74956693_t1.mp4')

    fp_getfpfile(filename,filename.split('/')[-1].split('.')[0]+'.afp',False,True)

def create_fp_bin_list(file_path):
    fp_list = fp_extract(file_path)
    new_fp_list = []
    for fp in fp_list:
        new_fp_list.append(fp_bin(fp))
    return new_fp_list
def save(fp_list,file_name):
    filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/temp/'+file_name)
    fo = open(filename, "wb")
    for index,fp in enumerate(fp_list):
        stringff = "%05d  %s\n" % (index,fp)
        fo.write(stringff);
    fo.close()

def fp_bin_bat():
    files_root=os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/test')
    file_list = get_dir_files(files_root)
    for filename in file_list:
        new_name = filename.split('/')[-1].split('.')[0]+'.afp'
        fp_list = create_fp_bin_list(filename)
        save(fp_list,new_name)


def get_video_length(filepath):
    output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),"../data/temp/"+random_str(20)+'video.info')
    sys_cmd_str = 'ffmpeg -i '+ filepath + ' 2>'+output_file
    os.system(sys_cmd_str)

    info_str = open(output_file).read()
    pattern = re.compile(r'Duration: ([\d]{2}:[\d]{2}:[\d]{2})')
    time_len = re.findall(pattern,info_str)
    os.remove(output_file)
    return standart_and_seconds(time_len[0])


#
# 音频分段函数，将指定文件夹下的音频分割成小段音频
def audio_extraction(allin_one=False,gap=60,files_root=None,extensions=None,out_files_root=None):
    filelist = get_dir_files(files_root,extensions)
    for file in filelist:
        filename = file.split('/')[-1].split('.')[0]
        file_time_len = get_video_length(file)
        print "%-26s%05ss:" % (filename,file_time_len),
        start = 0
        pre=-1
        t=gap
        while(start<file_time_len):
            if start+t > file_time_len:
                t = file_time_len - start
            if allin_one:
                t = file_time_len
            finish_ratio = int(100.0*(start+t)//file_time_len)
            if finish_ratio!=pre and finish_ratio%5==0:
                print finish_ratio,
                pre = finish_ratio

            new_filename = file.split('/')[-1].split('.')[0]
            if  not allin_one:
                new_filename += ("_%s_%s"%(start,start+t))

            new_out_files_root = out_files_root
            if not allin_one:
                new_out_files_root = out_files_root + '/'+filename
            log_file_name = os.path.join(os.path.dirname(os.path.abspath(__file__)),"../data/temp/"+random_str(20)+'temp.log')
            if  not os.path.exists(new_out_files_root):
                os.makedirs(new_out_files_root)

            out_files_path = new_out_files_root + '/'+new_filename+'.wav'
            if os.path.exists(out_files_path):
                start+=t
                continue
            sys_cmd_str = 'ffmpeg -i '+file+' -ar 44100 -ac 1 -ab 128 -f wav -ss '+ standart_and_seconds(start)+' -t '+ str(t) +' '+ out_files_path
            sys_cmd_str += ' 2>'+log_file_name
            os.system(sys_cmd_str)
            os.remove(log_file_name)
            start += t
        print ''

if __name__ == '__main__':


    # create_fp_file()
    # create_fp_test()
    # fp_bin_bat()

    files_root=os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/wanglei/TS')
    out_files_root=os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/wanglei/TEST')
    audio_extraction(allin_one=False,gap=5,files_root=files_root,extensions=['mkv','wav'],out_files_root=out_files_root)
    pass

