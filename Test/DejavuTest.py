#!/usr/bin/python
# -*- coding: UTF-8 -*-
import warnings
import json
import os
warnings.filterwarnings("ignore")

from Models.Tools import *

from dejavu import Dejavu
from dejavu import fingerprint,decoder

config= {
    "database": {
        "host": "127.0.0.1",
        "user": "root",
        "passwd": "root",
        "db": "dejavu2"
    }
}


def fingerprint_op(files_root,extensions):
    djv = Dejavu(config)
    djv.fingerprint_directory(files_root, extensions,nprocesses=1)

    #16.5小时节目 + 100首歌曲 , 指纹16161748,分割成曲目6136首

def fp_printing(filename):
    songname, extension = os.path.splitext(os.path.basename(filename))
    channels, Fs, file_hash = decoder.read(filename, None)
    result = set()
    channel_amount = len(channels)

    for channeln, channel in enumerate(channels):
        # TODO: Remove prints or change them into optional logging.
        print("Fingerprinting channel %d/%d for %s" % (channeln + 1, channel_amount, filename))
        hashes = fingerprint.fingerprint(channel, Fs=Fs)
        print("Finished channel %d/%d for %s" % (channeln + 1, channel_amount, filename))
        result |= set(hashes)
    return song_name, result, file_hash
if __name__ == '__main__':

    # files_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/songs')
    # fingerprint_op(files_root,['mp3'])
    pass
    filename = '/Users/simon/Documents/WORKSTATION/WorkSpaces/PyCharm/ListenTV/data/songs/haoguniang_R_01.mp3'

    fp_printing(filename)

