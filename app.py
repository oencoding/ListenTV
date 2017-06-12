#!/usr/bin/python
# -*- coding: utf-8 -*-
from flask import Flask, jsonify, render_template,request, redirect
import os
from Models.FPUnities import random_str

from Services.FPService import match_fp_service,dejavu_match_service
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.dirname(os.path.abspath(__file__)) + "/data/temp"


@app.route("/")
def welcome():
    return render_template('index.html')

#接受搜索请求API，返回推断信息
@app.route("/find_voice", methods=['GET','POST'])
def find_voice():
    result = {'state':1,'rspcode':200, 'info':'success'}
    if not request.method == 'POST':
        result['state'] = 0
        result['rspcode'] = 403
        result['info'] = "请使用post方法"
        return jsonify(result)
    file = request.files['voice_file']
    if not file :
        result['state'] = 0
        result['rspcode'] = 403
        result['info'] = "录音文件域为空"
        return jsonify(result)
    filename = random_str(32) + file.filename
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    try:
        filename = random_str(32) + file.filename

        file.save(file_path)
    except Exception:

        result['state'] = 0
        result['rspcode'] = 501
        result['info'] = "服务器文件接受失败"
        return jsonify(result)

    inference_result = {}
    try:
        # inference_result = match_fp_service(file_path)
        inference_result = dejavu_match_service(file_path)
        # os.remove(file_path)
    except Exception:
        raise
        result['state'] = 0
        result['rspcode'] = 502
        result['info'] = "服务器发生异常了"
        return jsonify(result)
    result['info'] = "识别成功"
    result['data'] = inference_result
    return jsonify(result)

#接收节目详情查询请求，返回正在播放的节目清单
@app.route("/find_playlist")
def find_playlist():
    return "find_playlist"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=1115, debug=True)