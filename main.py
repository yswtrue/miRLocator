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


@app.errorhandler(Exception)
def handle_invalid_usage(error):
    status_code = error.status_code if hasattr(error, 'status_code') else 500
    response = jsonify({'code': status_code, 'message': error.message})
    response.status_code = status_code
    return response


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        now_datetime = datetime.datetime.now().strftime('%Y-%m-%d%H:%M:%S')
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], now_datetime)
        # upload_path = app.config['UPLOAD_FOLDER']
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

        lib.resultDic = lib.resultDic + now_datetime + '/'

        # 开始执行文件
        lib.start(training_data_path, prediction_data_path,
                  prediction_data_annotated_path)
        with open(lib.resultDic + 'miRLocator_predResults.txt',
                  'r') as result_file:
            first_line = result_file.readline()
            mi_rna = first_line.split('\t')[0]
            from subprocess import call
            try:
                call([
                    'convert', '{path}/{file_name}'.format(
                        path=os.path.join(lib.resultDic, 'dp_ss_pred'),
                        file_name=mi_rna + '_dp.ps'),
                    '{path}/result.png'.format(
                        path=os.path.join(lib.resultDic, 'dp_ss_pred'))
                ])
            except OSError as e:
                if e.errno == os.errno.ENOENT:
                    raise Exception('没有安装imagemagick')
                raise e

            return jsonify({
                'first_line': first_line,
                'png_path': '/static/results/dp_ss_pred/result.png'
            })
        # 获取结果的第一行，然后现实既可以了

        return jsonify()
    else:
        # 显示首页
        return render_template('index.html')


if __name__ == '__main__':
    app.run()
