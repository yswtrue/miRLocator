#!env python
# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify, Response, json, send_from_directory, render_template
import source
import lib
import os, sys
import datetime
import zipfile
import pprint
from subprocess import call

__dir__ = os.getcwd()
UPLOAD_FOLDER = os.path.join(__dir__, 'upload')
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# @app.errorhandler(Exception)
def handle_invalid_usage(error):
    status_code = error.status_code if hasattr(error, 'status_code') else 500
    response = jsonify({'code': status_code, 'message': error.message})
    response.status_code = status_code
    return response


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        now_datetime = datetime.datetime.now().strftime('%Y-%m-%d%H:%M:%S')
        # now_datetime = ''
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

        lib.resultDic = lib.sourceDic + "static/results/" + now_datetime + '/'

        # 开始执行文件
        lib.start(training_data_path, prediction_data_path,
                  prediction_data_annotated_path)
        results = []
        with open(lib.resultDic + 'miRLocator_predResults.txt',
                  'r') as result_file:
            # 获取转换后的文件内容
            lines = result_file.readlines()
            # 把每行的内容转化为html
            for i, line in enumerate(lines):
                # 获取文件名
                mi_rna = line.split('\t')[0]
                png_url = '{path}/{name}.png'.format(
                    path=os.path.join('static/results', now_datetime,
                                      'dp_ss_pred'),
                    name=mi_rna)
                png_path = os.path.join(__dir__, png_url)
                # 获取需要生成的html地址
                html_url = '{path}/{name}.html'.format(
                    path=os.path.join('static/results', now_datetime,
                                      'dp_ss_pred'),
                    name=mi_rna)
                html_path = os.path.join(__dir__, html_url)
                tmp = {
                    'mi_rna': mi_rna,
                    'line': line.split('\t'),
                    'img_url': '{}.png'.format(mi_rna),
                    'html_url': '/' + html_url
                }
                # 输出html
                context = render_template('pages.html', **tmp)
                try:
                    with open(html_path, 'w') as html:
                        html.write(context.encode('utf-8'))
                    pass
                except Exception as e:
                    raise e

                # 转化图片
                try:
                    call([
                        'convert', '{path}/{file_name}'.format(
                            path=os.path.join(lib.resultDic, 'dp_ss_pred'),
                            file_name=mi_rna + '_dp.ps'), png_path
                    ])
                except OSError as e:
                    if e.errno == os.errno.ENOENT:
                        raise Exception('没有安装imagemagick')
                    raise e
                except Exception as e:
                    raise e
                results.append(tmp)
            # 打包结果
            zip_file_path = os.path.join(lib.resultDic, 'results.zip')

            lib.zipdir(lib.resultDic, zip_file_path)
            return jsonify({
                'lines':
                results,
                'zip_file_path':
                '/static/results/' + now_datetime + '/results.zip',
            })

    else:
        # 显示首页
        return render_template('index.html')


if __name__ == '__main__':
    app.run()
