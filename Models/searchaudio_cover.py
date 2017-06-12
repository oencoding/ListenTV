#!/usr/bin/env python
import os
import re
import time
import sys
from optparse import OptionParser
import Config
import redis
from Models.SerachAudioUnities import *
CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))
num_windows = 0
def countbits(value):
    cnt = 0
    for i in range(32):
        if (value>>i)&1:
            cnt +=1
    return cnt
def countpatch(value):
    cnt = 0
    for i in range(31):
        tmp = (value>>i)&3
        if tmp == 1 or tmp == 2:
            cnt += 1
    return cnt
mask_map = []
level = []
judge_type = 'seque'
def init_mask_map(bits):
    mask_map.append(0)
    level.append(len(mask_map))
    for idx in range(bits):
        mask_map.append(1 << idx)
    level.append(len(mask_map))
    for idx in range(bits):
        mask = 1 << idx
        for jdx in range(idx):
            rmask = mask | 1 << jdx
            mask_map.append(rmask)
    level.append(len(mask_map))
    for idx in range(bits):
        mask1 = 1<<idx
        for jdx in range(idx):
            mask2 = mask1 | 1 << jdx
            for kdx in range(jdx):
                mask3 = mask2 | 1 << kdx
                mask_map.append(mask3)
    level.append(len(mask_map))
    #for mask in mask_map:
    #    print ('%x' % mask)
    print (level)

redis_pool = None
redis_host = None
redis_port = None
redis_handle = None

def do_connect():
    global redis_pool
    global redis_host
    global redis_port
    global redis_handle
    try:
        print redis_host
        print redis_port
#        if redis_pool == None:
#            redis_pool = redis.ConnectionPool(host=redis_host, port=redis_port)
        if redis_handle == None:
             redis_handle = redis.Redis(host=Config.SEARCH_AUDIO_DB_HOST, port=Config.SEARCH_AUDIO_DB_PORT, db=Config.SEARCH_AUDIO_DB_ID)
#        redis_handle = redis.StrictRedis(connection_pool=redis_pool)
        if redis_handle == None:
            raise 'redis_handle None.'
    except Exception, ex:
        print str(ex)

def filter(value):
    #return True
    if countbits(value) < 3 or countbits(value) > 29:
        return True
    if countpatch(value) < 4:
        return True
    return False

class RetrivalVideoWorker:
    def __init__(self,options):
        self.feature = options['feature']
        self.output  = options['output']
        # self.step    = options['step']
        self.hasht   = int(options['hashd'])
        #####
        self.split_step = 1500
        self.segs_match_thres = 4   # about 20% match
        self.num_segs = 0
        self.num_features_in_file = 0
        #use for segs#
        self.candis = {}
        self.seg_match_nums = {}
        self.scards = []
        self.segs_feat_list = []
        ##collect info
        self.num_feature_match = {}
        self.num_tseq_feat_match = {}
        
        self.match_video_dict = {}
        self.match_thres = 0.1
        #extend
        self.max_winNo = 1
        self.cover_width = 2*50*2 #2 mean left:right side
        self.forword_step = 4*50 # 50windows equal about 1s 
        self.seg_seqlist_dict = {}
        self.seqlist_dict = {}
        
        pass
    def reset_buffer_used(self):

        self.candis = {}
        self.seg_match_nums = {}
        self.scards = []
        self.seg_seqlist_dict = {}
        
    def __do_load_feature_key(self):
        # features = []
        # with open(self.feature) as f:
        #     for line in f.readlines():
        #         tt = re.findall(r'\d+',line)
        #         if len(tt) > 1:
        #             item = (int(tt[0]),int(tt[1]))
        #             features.append(item)
        # f.close()

        features = fp_extract(self.feature)

        self.num_features_in_file = len(features)
        return features
    
    def __split_feature_list(self,feature_list):
        step = self.split_step
        len_feature_list = len(feature_list)
        #print "step = %d end = %d "%(step,end)
        last = 0
        thres = self.split_step
        sub_list = []
        for i in range(len_feature_list):
            winNo = feature_list[i][0]
            if winNo >= thres:
               sub_list = feature_list[last:i]
               self.segs_feat_list.append(sub_list)
               thres +=self.split_step
               last = i
               #print sub_list
        sub_list = feature_list[last:]
        self.segs_feat_list.append(sub_list)  
        #print sub_list
        #record num of feat
        self.num_segs = len(self.segs_feat_list)
        print "num of segs = %d" %self.num_segs
        
    def __query_features_from_db(self,features):
        pipe = redis_handle.pipeline()
        for feature in features:
            pipe.scard(feature[1])
        scards = pipe.execute()
        
        ft_idx = 0
        #print ""
        for feature_t in features:
            feature = feature_t[1]
            f_idx = feature_t[0]
            self.max_winNo = max(self.max_winNo,float(f_idx))
            #print '%d,%d'%(f_idx,feature),
            if scards[ft_idx] > self.hasht:
                ft_idx += 1
                continue
            ft_idx += 1
            union = []
            for i in range(level[int(options['level'])]):
                feature = feature ^ mask_map[i]
                if not filter(feature):
                    union.append(feature)

            if len(union) < 1:
                continue
            
            results = redis_handle.sunion(union)
            #print 'unios %d, feature %d' % (len(results), feature)
#            self.__classify_dbInfo_by_vid(results,f_idxi)
            self.__classify_dbInfo_by_vid(results,f_idx,feature_t)
        
#    def __classify_dbInfo_by_vid(self,results,f_idx):
    def __classify_dbInfo_by_vid(self,results,f_idx,feature_t):
        candis = self.candis
        seg_seqlist_dict = self.seg_seqlist_dict
        num_feature_match = self.num_feature_match
        for item in results:
            value = re.findall('(\d+)', item)
            deltaT = int(value[1]) - f_idx
            if not candis.has_key(value[0]):
                candis[value[0]] = {}
                seg_seqlist_dict[value[0]] = {}
            candis[value[0]][deltaT] = candis[value[0]].get(deltaT, 0) + 1
            
            if not seg_seqlist_dict[value[0]].has_key(deltaT):
                seg_seqlist_dict[value[0]][deltaT] = []
            seg_seqlist_dict[value[0]][deltaT].append(f_idx)
             
            num_feature_match[value[0]] = num_feature_match.get(value[0], 0) + 1
            outfile = options['output'] + value[0]
            #os.system('echo -e "%d %s" >> %s' % (f_idx, value[1], outfile))    
    def __find_max_timedomain_match(self):
        num_tseq_feat_match = self.num_tseq_feat_match 
        candis = self.candis
        seqlist_dict = self.seqlist_dict
        seg_seqlist_dict = self.seg_seqlist_dict
        segs_match_results = {}
        feat_match = {} 
        for vid,candi in candis.items():
            #print vid
            max_c = 1
            max_k = 0
            if judge_type == 'seque':
                for k,c in candi.items():
                    #print c
                    for idx in range(int(8)):
                        c = c + candi.get(k + idx + 1, 0)
                        c = c + candi.get(k - idx - 1, 0)
                    if c > max_c:
                        max_c = c
                        max_k = k
            else:
                max_c = 0
                for k,c in candi.items():
                    max_c += c 
            if max_c > 1:
                #print max_c
                segs_match_results[vid] = max_c
                num_tseq_feat_match[vid] = num_tseq_feat_match.get(vid, 0) + max_c
                feat_match[vid] = feat_match.get(vid, 0) + max_c
            if not seqlist_dict.has_key(vid):
                seqlist_dict[vid] = []

            if seg_seqlist_dict[vid].has_key(max_k):
                seqlist_dict[vid].extend(seg_seqlist_dict[vid][max_k])
            for idx in range(int(8)):
                left_idx = max_k-idx-1
                right_idx = max_k+idx+1
                #if vid == "79890769":
                    #print len(seqlist_dict)
                if seg_seqlist_dict[vid].has_key(left_idx):
                    seqlist_dict[vid].extend(seg_seqlist_dict[vid][left_idx])
                if seg_seqlist_dict[vid].has_key(right_idx):
                    seqlist_dict[vid].extend(seg_seqlist_dict[vid][right_idx])
            #if vid == "79890769":
                #print max_c
                #print seqlist_dict[vid]
        
        #for k,v in feat_match.items():
        #   print (k,v)
        #print len(num_tseq_feat_match) 
        self.seg_match_nums = segs_match_results
        
    def __get_similar_list(self):
        pThres = self.match_thres
        seqlist_dict = self.seqlist_dict
        cover_width = self.cover_width 
        forword_step =self.forword_step
        match_video_dict = self.match_video_dict
        
        
        for vid,seqlist in seqlist_dict.items():
            #print vid,self.num_feature_match[vid],len(seqlist)
            if len(seqlist) < 4:
                continue
            end_pos = 0
            cover = 0
            last_item = None
            curr_item = None
            seqlist.sort()
            #print 'hwh',len(seqlist)
            for item in seqlist:
                curr_item = int(item)
                end_pos = curr_item + cover_width/2
                if last_item == None:
                    last_item = curr_item
                    d_value = min(last_item,cover_width/2)
                    cover += (d_value + cover_width/2)
                    continue
                d_value = curr_item - last_item
                if d_value <= forword_step:
                    cover += d_value
                else:
                    cover += cover_width
                last_item = curr_item
            if end_pos > self.max_winNo:
                cover -= (end_pos-self.max_winNo)
            p = cover/self.max_winNo
            #print cover,self.max_winNo,p
            if p >= pThres:
                match_video_dict[vid] = p
        
    def __output_retrival_result(self):
        match_video_dict = self.match_video_dict
        results = sorted(match_video_dict.items(), key=lambda x: x[1], reverse=True)
        
        total = self.num_features_in_file 
        num_feature_match = self.num_feature_match 
        num_tseq_feat_match =self.num_tseq_feat_match 
        
        with open(self.output, "w") as rh:
            rh.write('total %d\n' % total)
            for result in results:
                vid = result[0]
                score = result[1]*100
                matchs = num_feature_match[vid] + 0.1
                sequence = num_tseq_feat_match[vid]
                rh.write('%s %0.1f%s: matchs %d, sequency %d,  sequency/matchs %.2f\n'\
                         % (vid,score,'%', matchs, sequence, sequence/matchs))
                print ('%s %0.1f%s: matchs %d, sequency %d,  sequency/matchs %.2f'\
                         % (vid,score,'%', matchs, sequence, sequence/matchs))
        rh.close()
    def do_retrival(self):
        match_histogram = {}
        
        feature_list = self.__do_load_feature_key()
        self.__split_feature_list(feature_list)
        
        for subList in self.segs_feat_list:
            #print 'len of sublist = %d'%len(subList)
            self.reset_buffer_used()
            self.__query_features_from_db(subList)
            self.__find_max_timedomain_match()

        self.__get_similar_list()            
        self.__output_retrival_result()
        
    
    
if __name__ == '__main__':

    filename = os.path.join(os.path.dirname(os.path.abspath(__file__)),'../data/wenhan/source2_rec_test/87142686_rec_01.mp3')

    options = {}
    options["feature"] = filename
    options["output"] = '../data/temp/'+filename.split('/')[-1].split('.')[0]+'_matchresult.txt'
    options["hashd"] = 500
    options['level'] = 1
    options['judge'] = 'seque'


    time_start = time.clock()
    judge_type = options['judge']
    init_mask_map(32)
    do_connect()
    ss = RetrivalVideoWorker(options)
    ss.do_retrival()
    time_stop = time.clock()
    print 'time cost : %d' % (time_stop - time_start)
