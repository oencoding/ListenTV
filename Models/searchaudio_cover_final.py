#!/usr/bin/env python
import os
import re
import logging
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

def filter(value):
    #return True
    if countbits(value) < 3 or countbits(value) > 29:
        return True
    if countpatch(value) < 4:
        return True
    return False

def get_redis_handle():
    try:
        redis_handle = redis.Redis(host=Config.SEARCH_AUDIO_DB_HOST,port=Config.SEARCH_AUDIO_DB_PORT,db=int(Config.SEARCH_AUDIO_DB_ID))
        if redis_handle == None:
            raise 'redis_handle None.'
    except Exception, ex:
        print str(ex)
    return redis_handle

class SearchAudio:
    def __init__(self,options):
        self.feature = options["feature"]
        self.output  = options["output"]
        self.step    = 1
        self.hasht   = options["hasht"]
        self.redis_handle = options["redis_handle"]
        self.level   =  options["level"]
        logging.debug('feat:%s,output%s'%(self.feature,self.output))
        #use for segs#
        self.candis = {}
        ##collect info
        self.match_thres = 0.3
        #extend
        self.max_winNo = 1
        self.deltaT_seqlist_dict = {}
        self.seqlist_dict = {}
        self.num_tseq_feat_match = {}
        #v2
        self.cover_list = {}
        self.cover_len  = {}
        self.match_video_dict = {}
        self.num_feature_match= {}
        self.r = 5
        self.tc = 5
        #
        self.match_video_start_point = {} 
        self.forword_step_p = 0.1
        self.cover_width = 2*50#*2 #2 mean left:right side
        self.num_query_feat = 0
        if len(mask_map) == 0:
            init_mask_map(32) 
    def __do_load_feature_key(self):
        features = fp_extract(self.feature)
        self.num_features_in_file = len(features)
        self.num_query_feat = len(features)
        return features
    def get_numfeats_in_file(self):
        return self.num_query_feat

    def __query_features_from_db(self,features):
        logging.debug('2.1')        
        pipe = self.redis_handle.pipeline()
        for feature in features:
            pipe.scard(feature[1])
        scards = pipe.execute()
        
        logging.debug('2.2,%d'%len(mask_map))        
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
            for i in range(level[int(self.level)]):
                feature = feature ^ mask_map[i]
                if not filter(feature):
                    union.append(feature)
            if len(union) < 1:
                continue
            
            results = self.redis_handle.sunion(union)
            #print 'unios %d, feature %d' % (len(results), feature)
#            self.__classify_dbInfo_by_vid(results,f_idxi)
            self.__classify_dbInfo_by_vid(results,f_idx,feature_t)
        logging.debug('2.3')        
        
#    def __classify_dbInfo_by_vid(self,results,f_idx):
    def __classify_dbInfo_by_vid(self,results,f_idx,feature_t):
        candis = self.candis
        deltaT_seqlist_dict = self.deltaT_seqlist_dict
        for item in results:
            #value = re.findall('(\d+)', item)
            value = item.split(',')
            deltaT = int(value[1]) - f_idx #value[1]:time, value[0]:vid
            if not candis.has_key(value[0]):
                candis[value[0]] = {}
                deltaT_seqlist_dict[value[0]] = {}
            candis[value[0]][deltaT] = candis[value[0]].get(deltaT, 0) + 1
            
            if not deltaT_seqlist_dict[value[0]].has_key(deltaT):
                deltaT_seqlist_dict[value[0]][deltaT] = []
            deltaT_seqlist_dict[value[0]][deltaT].append((f_idx,int(value[1])))#20160120 add match time in vid 

    def __find_time_matchSegs_inCandi(self,vid,candi):
            max_c = 1
            max_k = 0
            if judge_type == 'seque':
                for k,c in candi.items():
                    #print c
                    for idx in range(int(self.r)):
                        c = c + candi.get(k + idx + 1, 0)
                        c = c + candi.get(k - idx - 1, 0)
                    if c > max_c:
                        max_c = c
                        max_k = k
            else:
                max_c = 0
                for k,c in candi.items():
                    max_c += c 
            return max_c,max_k
        
    def __pop_maxK_interval_inCandi(self,max_k,candi):
        if candi.has_key(max_k):
            candi.pop(max_k)
        for idx in range(int(self.r)):
            left_idx = max_k-idx-1
            right_idx = max_k+idx+1
            if candi.has_key(left_idx):
                candi.pop(left_idx)
            if candi.has_key(right_idx):
                candi.pop(right_idx)
        
    #save cover area
    def __collect_points_inSeg(self,vid,max_k):
        left_bound = 9999999
        right_bound = -1
        deltaT_seqlist_dict = self.deltaT_seqlist_dict
        seqlist_dict = self.seqlist_dict
        min_t = left_bound
        max_t = -1 
        if deltaT_seqlist_dict[vid].has_key(max_k):
            min_t = deltaT_seqlist_dict[vid][max_k][0][0]
            max_t = deltaT_seqlist_dict[vid][max_k][-1][0]
        
        for idx in range(int(self.r)):
            left_idx = max_k-idx-1
            right_idx = max_k+idx+1
            ##left##
            if deltaT_seqlist_dict[vid].has_key(left_idx):
            ##(query_idx,candi_idx)
                if min_t > deltaT_seqlist_dict[vid][left_idx][0][0]:
                    min_t = deltaT_seqlist_dict[vid][left_idx][0][0]
                if max_t < deltaT_seqlist_dict[vid][left_idx][-1][0]:
                    max_t = deltaT_seqlist_dict[vid][left_idx][-1][0] 
            ##right##
            if deltaT_seqlist_dict[vid].has_key(right_idx):
                if min_t > deltaT_seqlist_dict[vid][right_idx][0][0]:
                    min_t = deltaT_seqlist_dict[vid][right_idx][0][0]
                if max_t < deltaT_seqlist_dict[vid][right_idx][-1][0]:
                    max_t = deltaT_seqlist_dict[vid][right_idx][-1][0]
        if (max_t - min_t + 0.1)/self.max_winNo < 0.1:
            #print "less:%s %s"%((max_t - min_t),(max_t - min_t + 0.1)/self.max_winNo)
            return
        
        if not seqlist_dict.has_key(vid):
            seqlist_dict[vid] = []
        if deltaT_seqlist_dict[vid].has_key(max_k):
            seqlist_dict[vid].extend(deltaT_seqlist_dict[vid][max_k])
            deltaT_seqlist_dict[vid].pop(max_k)
                   
        for idx in range(int(self.r)):
            left_idx = max_k-idx-1
            right_idx = max_k+idx+1
            ##left##
            if deltaT_seqlist_dict[vid].has_key(left_idx):
                seqlist_dict[vid].extend(deltaT_seqlist_dict[vid][left_idx])
                deltaT_seqlist_dict[vid].pop(left_idx)
            ##right##
            if deltaT_seqlist_dict[vid].has_key(right_idx):
                seqlist_dict[vid].extend(deltaT_seqlist_dict[vid][right_idx])
                deltaT_seqlist_dict[vid].pop(right_idx)
        #print seqlist_dict[vid]
    def __find_match_segs(self):
        
        num_tseq_feat_match = self.num_tseq_feat_match 
        candis = self.candis
        for vid,candi in candis.items():
            #print vid
            thres_c = self.tc
            max_c = thres_c
            total_c = 0
            while max_c >= thres_c:
                max_c,max_k = self.__find_time_matchSegs_inCandi(vid,candi)
                self.__pop_maxK_interval_inCandi(max_k,candi)
                if max_c >=thres_c:
                    self.__collect_points_inSeg(vid, max_k)
                    total_c += max_c
            if total_c >= thres_c:
                num_tseq_feat_match[vid] = num_tseq_feat_match.get(vid, 0) + total_c
                
    def __deal_cover_list_conflict(self):
        for vid,segs in self.cover_list.iteritems():
            #print vid,len(segs)
            tlist = sorted(segs,key=lambda x:x[0])
            for item in tlist:
                #print item[0]/50.0,item[1]/50.0,(item[1]-item[0])/50.0,item[2],",",
                print (item[1]-item[0])/50.0,",",
            print ""
            last_l = tlist[0][0]
            last_r = tlist[0][1]
            for i in range(len(tlist)):
                curr_l = tlist[i][0]
                curr_r = tlist[i][1]
                if curr_l >= last_r:
                    self.cover_len[vid] = self.cover_len.get(vid,0) + (last_r - last_l)
                    last_l = curr_l
                    last_r = curr_r
                else:
                    if curr_r > last_r:
                        self.cover_len[vid] = self.cover_len.get(vid,0) + (curr_l - last_l)
                        last_l = curr_l
                        last_r = curr_r
            self.cover_len[vid] = self.cover_len.get(vid,0) + (last_r - last_l)   
    def __get_similar_list(self):
        pThres = self.match_thres
        seqlist_dict = self.seqlist_dict
        cover_width = self.cover_width 
        forword_step =self.forword_step_p * self.max_winNo
        match_video_dict = self.match_video_dict
        match_video_start_point = self.match_video_start_point 
        #print len(seqlist_dict.items())
        counter = 0 
        for vid,seqlist in seqlist_dict.items():
            #print vid,self.num_feature_match[vid],len(seqlist)
            #print seqlist
            if len(seqlist) < 2:
                counter +=1
                continue
            end_pos = 0
            cover = 0
            last_item = None
            curr_item = None
            seqlist.sort(key=lambda x:x[0])#20160120 add match time in vid
            #print 'hwh',len(seqlist)
            for item in seqlist:
                curr_item = int(item[0])
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
                    tt = min(d_value,cover_width)
                    cover += tt
                last_item = curr_item
                #print curr_item,d_value,cover,forword_step,self.max_winNo
            if end_pos > self.max_winNo:
                cover -= (end_pos-self.max_winNo)
            p = cover/self.max_winNo
            print cover,self.max_winNo,"%0.2f"%p
            if p >= pThres:
                match_video_dict[vid] = p
                match_video_start_point[vid] = seqlist#20160120 add match time in vid
        #print counter
                
    def __output_retrival_result(self):
        match_video_dict = self.match_video_dict
        results = sorted(match_video_dict.items(), key=lambda x: x[1], reverse=True)

        total = self.num_features_in_file
        num_tseq_feat_match =self.num_tseq_feat_match 
        
        match_video_start_point = self.match_video_start_point
        with open(self.output, "w") as rh:
            #rh.write('total %d\n' % total)
            for result in results:
                vid = result[0]
                score = result[1]*100
                matchs = num_tseq_feat_match[vid] + 0.1
                
                start_point_in_query = match_video_start_point[vid][0][0]/50
                start_point_in_match = match_video_start_point[vid][0][1]/50
                rh.write('%s %0.1f %d %d %d '\
                     % (vid,score, start_point_in_query,start_point_in_match,self.max_winNo/50))
                #logging.info(match_video_start_point[vid])
                for item in match_video_start_point[vid]:
                    rh.write('(%d,%d)'%(item[0]/50,item[1]/50))
                rh.write('\n')
                print ('%s %0.1f%s: matchs %d'\
                         % (vid,score,'%', matchs))
        rh.close()
    def do_retrival(self):
        feature_list = self.__do_load_feature_key()
        self.__query_features_from_db(feature_list)
        self.__find_match_segs()
        self.__deal_cover_list_conflict()
        self.__get_similar_list()           
        self.__output_retrival_result()

def bat_test():
    files_root=os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/test')
    # files_root=os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/wenhan/source2_rm_rec_test')
    # files_root=os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/wenhan/source2_ip_rec_test')
    # files_root=os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/wenhan/source2_vol_down_test')
    file_list = get_dir_files(files_root)

    for filename in file_list:
        print filename.split('/')[-1].split('.')[0]+':'
        options = {}
        options["feature"] = filename
        options["output"] =  '../data/temp/'+filename.split('/')[-1].split('.')[0]+'_matchresult.txt'
        options["hasht"] = 500
        options["level"] = 1
        options["redis_handle"] = get_redis_handle()

        sa = SearchAudio(options)
        sa.do_retrival()
        print '\n'

def main_test():
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


    # filename = os.path.join(os.path.dirname(os.path.abspath(__file__)),'../data/wenhan/source2_rec_test/87121420_rec_01.mp3')
    # filename = os.path.join(os.path.dirname(os.path.abspath(__file__)),'../data/wenhan/source2_rec_test/87126757_rec_01.mp3')
    filename = os.path.join(os.path.dirname(os.path.abspath(__file__)),'../data/wenhan/source2_rm_rec_test/87142686_rec_01.mp3')

    options = {}
    options["feature"] = filename
    options["output"] =  '../data/temp/'+filename.split('/')[-1].split('.')[0]+'_matchresult.txt'
    options["hasht"] = 500
    options["level"] = 1
    options["redis_handle"] = get_redis_handle()

    sa = SearchAudio(options)
    sa.do_retrival()

if __name__ == '__main__':
    bat_test()
    # main_test()