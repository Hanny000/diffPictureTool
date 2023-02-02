import base64
import json
import os
from ast import literal_eval

import cv2
import imutils
import numpy as np
from flask import Flask, jsonify, request
from skimage.metrics import structural_similarity

from backend.format_converter import file_to_base64, base64_to_bytes, image2byte, base64_to_image, base64_to_file

app = Flask(__name__)


def excute(pic_name, base64_of_old_pic=None, base64_of_new_pic=None):
    '''
    这个数组用于存放测试完的图片的数据
    第一个值放测试结果，第二个值放图片名，第三个值和第四个值对应这个用这个方法返回的两张图的二进制代码
    这些会在展示测试结果的tab那边用到
    '''
    result = {}
    try:
        # byte2image 没啥好看的，就是二进制代码转回.png 的图片
        imageA = base64_to_image(base64_of_old_pic)
        imageB = base64_to_image(base64_of_new_pic)
        grayA = cv2.cvtColor(imageA, cv2.COLOR_BGR2GRAY)
        grayB = cv2.cvtColor(imageB, cv2.COLOR_BGR2GRAY)

        (score, diff) = structural_similarity(grayA, grayB, full=True)
        diff = (diff * 255).astype("uint8")
        if int(score) == 1:
            result["test_result"] = "pass"
            result["pic_name"] = pic_name
            result["base64_of_res"] = base64.b64encode(image2byte(imageB)).decode('utf8')
            result["base64_of_old_pic"] = base64.b64encode(image2byte(imageA)).decode('utf8')

        else:
            thresh = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
            cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cnts = cnts[1] if imutils.is_cv3() else cnts[0]

            for c in cnts:
                (x, y, w, h) = cv2.boundingRect(c)
                cv2.rectangle(imageA, (x, y), (x + w, y + h), (0, 0, 255), 2)
                cv2.rectangle(imageB, (x, y), (x + w, y + h), (0, 0, 255), 2)


            # cv2.imshow("Modified",imageB) #show image
            result["test_result"] = "fail"
            result["pic_name"] = pic_name
            result["base64_of_res"] = base64.b64encode(image2byte(imageB)).decode('utf8')
            result["base64_of_old_pic"] = base64.b64encode(image2byte(imageA)).decode('utf8')

            # cv2.imwrite("./result/"+resultName+'.png', imageB)
            # cv2.waitKey(0)
        return result
    except Exception as e:
        return str(e)

@app.route("/diffpicture", methods=['POST'])
def diff_picture():
    pic_name = request.json.get("pic_name")
    base64_of_new_pic = request.json.get("new_pic")
    base64_of_old_pic = request.json.get("old_pic")
    if 'new_pic' and "old_pic" and "pic_name" in request.json:
        res = excute(pic_name, base64_of_old_pic, base64_of_new_pic)
        if type(res) == str:
            return res, 400
        elif type(res) == dict:
            return res, 200
    else:
        return jsonify({"code": 404, "msg": "图像为空！！！"})

@app.route("/load_project", methods=['GET'])
def load_project():
    all_history = {}
    projects = os.listdir("../backend/history")
    for project in projects:
        release = os.listdir("./history/" + project)
        all_history[project] = release
    return all_history, 200

@app.route("/load_history_pic", methods=['GET'])
def load_history_pic():
    history_pic = {}
    project = request.values.to_dict().get("project")
    release = request.values.to_dict().get("release")
    history_path = "../backend/history/" + project + "/" + release
    for file_name in os.listdir(history_path):
        data = file_to_base64(history_path + "/" + file_name)
        history_pic[file_name] = data
    return history_pic, 200


@app.route("/save_pic", methods=['post'])
def save_pic():
    history_pic = {}
    project = request.json.get("project")
    release = request.json.get("release")
    images = request.json.get("images")
    path = "./history/%s/%s" % (project, release)
    if not os.path.exists(path):
        os.makedirs(path)
    else:
        return "already exist", 401
    for image_name in images.keys():
        image_bytes = base64.b64decode(images.get(image_name))
        with open(path + "/" + image_name, 'wb') as f:
            f.write(image_bytes)
    return "save success", 200

if __name__ == '__main__':
    # app.config['JSON_AS_ASCII'] = False
    app.run(port=5000)
