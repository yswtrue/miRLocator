#!env python
# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify, Response, json, send_from_directory
import source
import lib
import os, sys
import datetime
import zipfile

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'upload')
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # now_datetime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # upload_path = os.path.join(app.config['UPLOAD_FOLDER'], now_datetime)
        upload_path = app.config['UPLOAD_FOLDER']
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)
        # 判断文件
        if 'trainingData' not in request.files:
            raise Exception('没有trainingData.txt')
            # return Response(json.dumps({'code': 500, 'msg': '没有选择文件'}), 500)
        # 获取上传的文件
        training_data = request.files['trainingData']

        prediction_data = request.files.get('predictionData', None)
        prediction_data_annotated = request.files.get(
            'predictionData_Annotated', None)

        training_data_path = os.path.join(upload_path, training_data.filename)
        training_data.save(training_data_path)
        # 判断是否有predictionData文件
        prediction_data_path = os.path.join(upload_path, 'predictionData.txt')
        if prediction_data:
            prediction_data_path = os.path.join(upload_path,
                                                prediction_data.filename)
            prediction_data.save(prediction_data_path)
        if not os.path.exists(prediction_data_path):
            raise Exception('没有predictionData.txt')

        # 判断是否有predictionData_Annotated文件
        prediction_data_annotated_path = os.path.join(
            upload_path, 'predictionData_Annotated.txt')
        if prediction_data_annotated:
            prediction_data_annotated_path = os.path.join(
                upload_path, prediction_data_annotated.filename)
            prediction_data_annotated.save(prediction_data_annotated_path)
        if not os.path.exists(prediction_data_annotated_path):
            raise Exception('没有predictionData_Annotated.txt')
        try:
            lib.start(training_data_path, prediction_data_path,
                      prediction_data_annotated_path)
        except Exception as e:
            raise e
        # 获取结果的第一行，然后现实既可以了

        return jsonify()
    else:
        # 显示首页
        return render_template('index.html')


if __name__ == '__main__':
    app.run()
