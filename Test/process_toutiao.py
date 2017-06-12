#!/usr/bin/python
# -*- coding: utf-8 -*-
from functools import partial
from multiprocessing.pool import Pool
from itertools import chain
from time import time

from download import setup_download_dir, get_links, download_link


def main():
    ts = time()

    url1 = 'https://item.taobao.com/item.htm?spm=a217l.8087239.620352.3.512Gng&id=536843329282'
    url2 = 'https://item.taobao.com/item.htm?spm=a217l.8087239.620352.4.512Gng&id=44022485238'

    download_dir = setup_download_dir('process_imgs')
    links = list(chain(
        get_links(url1),
        get_links(url2),
    ))

    download = partial(download_link, download_dir)
    with Pool(8) as p:
        p.map(download, links)
    print('一共下载了 {} 张图片'.format(len(links)))
    print('Took {}s'.format(time() - ts))

if __name__ == '__main__':
    main()