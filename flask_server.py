from flask import Flask, request, jsonify
import json 
import cv2

from src.engine_opencv import Engine 
from src.face_database import FaceDatabase
from src.scrfd import SCRFD 
from src.face_align import norm_crop 
from src.face_recognition import FaceRecog

from src.utils import get_logger, convert_image_2_base64_str, HeartBeat
from src.grpc_client import GrpcClient

GLOBAL_INFO = {
    'triton_host': '127.0.0.1:8000',
    'face_detec_model_name': 'ensemble_scrfd',
    'face_recog_model_name': 'face_recog',
    'face_detec_thres1': 0.6,
    'face_detec_thres2': 0.8,
    'redis_host': '127.0.0.1',
    'redis_port': 7999,
    'face_database_thres': 0.35
}

app = Flask(__name__)

@app.route('/batch/add_source', methods=['POST'])
def batch_add_source():
    logger.info('batch add source ====>')
    try:
        logger.info(f'input: {request.get_json()}')
        result = {'code': 200}

        result['msg'] = ''
        tasks = request.get_json()
        for task in tasks:
            task_id = request.form['task_id']
            stream_url = request.form['rtsp_url']
            grpc_address = request.form.get('grpc_address', None)
            rtmp_address = request.form.get('rtmp_address', None)
            stream_frequency = request.form.get('frame_rate', 25)
            stream_frequency = int(stream_frequency)

            if task_id in task_list:
                result['code'] = 11001
                result['msg'] += f'duplicate task id{task_id}; '
            elif rtmp_address is not None and rtmp_address in rtmp_dict.values():
                result['code'] = -2
                result['msg'] += f'rtmp_adress {rtmp_address} already in task; '
            else:
                add_task(task_id, stream_url, grpc_address, rtmp_address, stream_frequency)
        result['source_list'] = list(task_list)
        return result 
    except Exception as e:
        return {'code': 500, 'msg': str(e)}

@app.route('/add_source', methods=['POST'])
def add_source():
    logger.info('add source ====>')
    try:
        logger.info(f'input: {request.form}')
        result = {'code': 200}

        task_id = request.form['task_id']
        stream_url = request.form['rtsp_url']
        grpc_address = request.form.get('grpc_address', None)
        rtmp_address = request.form.get('rtmp_address', None)
        stream_frequency = request.form.get('frame_rate', 25)
        stream_frequency = int(stream_frequency)

        if task_id in task_list:
            result['code'] = 11001
            result['msg'] = f'duplicate task id {task_id}'
        elif rtmp_address is not None and rtmp_address in rtmp_dict.values():
            result['code'] = -2
            result['msg'] = f'rtmp_adress {rtmp_address} already in task'
        else:
            add_task(task_id, stream_url, grpc_address, rtmp_address, stream_frequency)

        result['source_list'] = list(task_list)
        return result
    except Exception as e:
        return {'code': 500, 'msg': str(e)}

def add_task(task_id, stream_url, grpc_address, rtmp_address, stream_frequency):
    logger.info(f'add task task_id {task_id} ------')
    task_list.add(task_id)
    rtmp_dict[task_id] = rtmp_address 
    heart_beat_dict[task_id] = HeartBeat(task_id) 
    engine.add_source(stream_url, task_id, grpc_address, rtmp_address, \
        stream_frequency, heart_beat_dict[task_id])

@app.route('/remove_source', methods=['DELETE'])
def remove_source():
    logger.info('remove source ====>')
    try:
        logger.info(f'input: {request.form}')
        result = {'code': 200}

        task_id = request.form['task_id']

        if task_id not in task_list:
            result['code'] = 11000
            result['msg'] = f'can not find task id {task_id}'
        else:
            remove_task(task_id)

        result['source_list'] = list(task_list)
        return result
    except Exception as e:
        return {'code': 500, 'msg': str(e)}

def remove_task(task_id):
    if task_id in rtmp_dict.keys():
        rtmp_dict.pop(task_id)
    task_list.remove(task_id)
    heart_beat_dict.pop(task_id)

    engine.remove_source(task_id)    
    
@app.route('/get_source_list', methods=['POST'])
def get_source_list():
    logger.info('get source list ====>')
    return {'code': 200, 'source_list': list(task_list)}

@app.route('/source_status', methods=['POST'])
def source_status():
    logger.info('source_status ====>')
    try:
        logger.info(f'input: {request.get_json()}')
        task_ids = request.get_json()
        result = dict()
        
        for task_id in task_ids:
            heart_beat = heart_beat_dict.get(task_id, None) 
            if heart_beat is not None:
                result[task_id] = heart_beat.is_alive()
            else:
                result[task_id] = False

        logger.info(f'source status result: {result}')
        return {'code': 200, 'data': json.dumps(result)}
    except Exception as e:
        return {'code': 500, 'msg': str(e)}

@app.route('/rebuild_source', methods=['POST'])
def rebuild_source():
    logger.info('rebuild source ====>')
    try:
        logger.info(f'input: {request.form}')
        result = {'code': 200}

        task_id = request.form['task_id']
        stream_url = request.form['rtsp_url']
        grpc_address = request.form.get('grpc_address', None)
        rtmp_address = request.form.get('rtmp_address', None)
        stream_frequency = request.form.get('frame_rate', 25)
        stream_frequency = int(stream_frequency)

        if task_id in task_list:
            remove_task(task_id)
        add_task(task_id, stream_url, grpc_address, rtmp_address, stream_frequency)

        result['source_list'] = list(task_list)
        return result
    except Exception as e:
        return {'code': 500, 'msg': str(e)}

@app.route('/update_source', methods=['PUT'])
def update_source():
    logger.info('update source ====>')
    try:
        logger.info(f'input: {request.form}')
        result = {'code': 200}

        result['source_list'] = list(task_list)
        return result
    except Exception as e:
        return {'code': 500, 'msg': str(e)}

@app.route('/image_recog', methods=['POST'])
def image_recog():
    logger.info('image recog ====>')
    error_info = None 

    for i in range(20):
        try:
            logger.info(f'input: {request.form}')
            result = {'code': 200}

            img_url = request.form['img_url']

            result['face_data'] = []

            cap = cv2.VideoCapture(img_url)
            _, img = cap.read(cv2.IMREAD_IGNORE_ORIENTATION)
            if img is None:
                result['code'] = -1
                result['msg'] = f'img {img_url} is none'
            else:
                bboxes, kpss = scrfd.detect(img, GLOBAL_INFO['face_detec_thres1'])
                logger.info(f'face num in {img_url} is {len(bboxes)}')

                for bbox, kps in zip(bboxes, kpss):
                    face = norm_crop(img, kps)

                    features = face_recog.get_features([face])
                    top1 = face_recog.top1(features[0])

                    face_info = {}
                    face_info['name'] = top1[0]
                    face_info['conf'] = top1[1]  
                    face_info['bbox'] = bbox.tolist()
                    result['face_data'].append(face_info)

            return result

        except Exception as e:
            logger.error(f'try error, {i}, {str(e)}')
            error_info = str(e) 

    return {'code': 500, 'msg': str(error_info)}

@app.route('/add_face', methods=['POST'])
def add_face():
    logger.info('add face ====>')
    error_info = None 

    for i in range(10):
        try:
            logger.info(f'input: {request.form}')
            result = {'code': 200}

            face_name = request.form['face_name']
            img_url = request.form['img_url']
            grpc_address = request.form.get('grpc_address', None)
            cap = cv2.VideoCapture(img_url)
            _, img = cap.read(cv2.IMREAD_IGNORE_ORIENTATION)
            if img is None:
                result['code'] = -1
                result['msg'] = f'img {img_url} is none'
            elif face_name in face_database.keys():
                result['code'] = -2
                result['msg'] = f'face name {face_name} already in face database'
            else:
                bboxes, kpss = scrfd.detect(img, GLOBAL_INFO['face_detec_thres1'])
                logger.info(f'face num in {face_name} is {len(bboxes)} ------')

                if len(bboxes) ==  1:
                    face = norm_crop(img, kpss[0])
                    feature = face_recog.get_features([face])[0]

                    face_database.set(face_name, feature)

                    if grpc_address is not None:
                        try:
                            grpc_client = GrpcClient(grpc_address, -1)
                            result_details = {}
                            result_details['face_img_base64'] = convert_image_2_base64_str(face)
                            result_details['face_name'] = face_name
                            grpc_client.send_result(result_details)
                        except Exception as e:
                            logger.error(f'grpc error: {e}')

                    logger.info(f'face {face_name} added to redis ------')
                elif len(bboxes) == 0:
                    result['code'] = -2
                    result['msg'] = f'face num in {face_name} is 0'
                else:
                    result['code'] = -3
                    result['msg'] = f'face num in {face_name} is {len(bboxes)}'

            result['face_list'] = list(face_database.keys())
            return result
        except Exception as e:
            logger.error(f'try error, {i}, {str(e)}')   
            error_info = str(e) 

    return {'code': 500, 'msg': str(error_info)}

@app.route('/del_face', methods=['DELETE'])
def del_face():
    logger.info('delete face ====>')
    try:
        logger.info(f'input: {request.form}')
        result = {'code': 200}

        face_name = request.form['face_name']

        if face_name not in face_database.keys():
            result['code'] = -1
            result['msg'] = f'face_name {face_name} not in face list'
        else:
            face_database.delete(face_name)

        result['face_list'] = list(face_database.keys())
        return result
    except Exception as e:
        return {'code': 500, 'msg': str(e)}

@app.route('/get_face_list', methods=['POST'])
def get_face_list():
    logger.info('get face list ====>')
    return {'code': 200, 'face_list': list(face_database.keys())}

if __name__ == '__main__':
    face_database = FaceDatabase(GLOBAL_INFO['redis_host'], GLOBAL_INFO['redis_port'], GLOBAL_INFO['face_database_thres'])
    scrfd = SCRFD(GLOBAL_INFO['triton_host'], GLOBAL_INFO['face_detec_model_name']) 
    face_recog = FaceRecog(GLOBAL_INFO['triton_host'], GLOBAL_INFO['face_recog_model_name'])

    logger = get_logger('./logs')
    engine = Engine(logger, GLOBAL_INFO)

    rtmp_dict = {}
    task_list = set()
    heart_beat_dict = {}

    logger.info('start run server ------')
    app.run(host='0.0.0.0',port=5000)

