#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import os
import requests

from itertools import chain
from pathlib import Path

from bs4 import BeautifulSoup

# 结合 requests 和 bs4 解析出网页中的全部图片链接，返回一个包含全部图片链接的列表
def get_links(url):
    req = requests.get(url)
    soup = BeautifulSoup(req.text, "html.parser")
    return [img.attrs.get('data-src') for img in
            soup.find_all('div', class_='img-wrap')
            if img.attrs.get('data-src') is not None]

# 把图片下载到本地
def download_link(directory, link):
    img_name = '{}.jpg'.format(os.path.basename(link))
    download_path = directory / img_name
    r = requests.get(link)
    with download_path.open('wb') as fd:
            fd.write(r.content)

# 设置文件夹，文件夹名为传入的 directory 参数，若不存在会自动创建
def setup_download_dir(directory):
    download_dir = Path(directory)
    if not download_dir.exists():
        download_dir.mkdir()
    return download_dir