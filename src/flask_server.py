from flask import Flask, request 
import json 
import cv2
import argparse

from src.engine_opencv import Engine 
from src.face_align import norm_crop 

from src.utils import get_logger, convert_image_2_base64_str
from src.grpc_client import GrpcClient
from src.global_dict import gd

app = Flask(__name__)

@app.route('/add_source', methods=['POST'])
def add_source():
    logger.info('add source ====>')
    try:
        logger.info(f'input: {request.form}')
        result = {'code': 200}

        task_id = request.form['task_id']
        stream_url = request.form['rtsp_url']
        grpc_address = request.form.get('grpc_address', None)
        stream_frequency = request.form.get('frame_rate', 25)
        stream_frequency = int(stream_frequency)

        rule_info = request.form.get('rule_info', {})
        if rule_info: rule_info = json.loads(rule_info)
        if not isinstance(rule_info, dict): rule_info = {}

        if task_id in engine.task_dict.keys():
            result['code'] = 11001
            result['msg'] = f'duplicate task id {task_id}'
        else:
            logger.info(f'add task task_id {task_id} ------')
            engine.add_source(task_id, stream_url, grpc_address, stream_frequency, rule_info)

        result['source_list'] = list(engine.task_dict.keys())
        return result
    except Exception as e:
        logger.error(str(e))
        return {'code': 500, 'msg': str(e)}
    

@app.route('/remove_source', methods=['DELETE'])
def remove_source():
    logger.info('remove source ====>')
    try:
        logger.info(f'input: {request.form}')
        result = {'code': 200}

        task_id = request.form['task_id']

        if task_id not in engine.task_dict.keys():
            result['code'] = 200 #11000
            result['msg'] = f'can not find task id {task_id}'
        else:
            engine.remove_source(task_id)

        result['source_list'] = list(engine.task_dict.keys())
        return result
    except Exception as e:
        logger.error(str(e))
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
        stream_frequency = request.form.get('frame_rate', 25)
        stream_frequency = int(stream_frequency)

        rule_info = request.form.get('rule_info', {})
        if rule_info: rule_info = json.loads(rule_info)
        if not isinstance(rule_info, dict): rule_info = {}

        if task_id in engine.task_dict.keys():
            engine.remove_source(task_id)
        engine.add_source(task_id, stream_url, grpc_address, stream_frequency, rule_info)

        result['source_list'] = list(engine.task_dict.keys())
        return result
    except Exception as e:
        logger.error(str(e))
        return {'code': 500, 'msg': str(e)}

    
@app.route('/get_source_list', methods=['POST'])
def get_source_list():
    logger.info('get source list ====>')
    return {'code': 200, 'source_list': list(engine.task_dict.keys())}


@app.route('/source_status', methods=['POST'])
def source_status():
    logger.info('source_status ====>')
    try:
        logger.info(f'input: {request.get_json()}')
        task_ids = request.get_json()
        result = dict()
        
        for task_id in task_ids:
            heart_beat = gd.heart_beat_dict.get(task_id, None) 
            if heart_beat is not None:
                result[task_id] = heart_beat.is_alive()
            else:
                result[task_id] = False

        logger.info(f'source status result: {result}')
        return {'code': 200, 'data': json.dumps(result)}
    except Exception as e:
        logger.error(str(e))
        return {'code': 500, 'msg': str(e)}


@app.route('/update_source', methods=['PUT'])
def update_source():
    logger.info('update source ====>')
    try:
        logger.info(f'input: {request.form}')
        result = {'code': 200}

        task_id = request.form['task_id']
        if task_id not in engine.task_dict.keys():
            result['code'] = 200 #11000
            result['msg'] = f'can not find task id {task_id}'
        else:
            grpc_address = request.form.get('grpc_address', None)
            stream_frequency = request.form.get('frame_rate', 25)
            stream_frequency = int(stream_frequency)

            rule_info = request.form.get('rule_info', {})
            if rule_info: rule_info = json.loads(rule_info)
            if not isinstance(rule_info, dict): rule_info = {}

            gd.update_task(task_id, grpc_address, stream_frequency, rule_info)

        result['source_list'] = list(engine.task_dict.keys())
        return result
    except Exception as e:
        logger.error(str(e))
        return {'code': 500, 'msg': str(e)}


@app.route('/stream/pipe', methods=['POST'])
def create_push_stream_pipe():
    logger.info('create push stream pipe ====>')
    try:
        logger.info(f'input: {request.get_json()}')
        result = {'code': 200}
        
        ids = request.get_json()
        result['msg'] = f'input task ids: {ids}, create success ids:'
        for task_id in ids:
            task_id = str(task_id)

            if task_id in engine.task_dict.keys():
                gd.create_push_stream_pipe(task_id, args.rtmp_server_uri)
                result['msg'] = f'{result["msg"]} {task_id}'

        return result
    except Exception as e:
        logger.error(str(e))
        return {'code': 500, 'msg': str(e)}


@app.route('/stream/pipe', methods=['DELETE'])
def remove_push_stream_pipe():
    logger.info('remove push stream pipe ====>')
    try:
        logger.info(f'input: {request.get_json()}')
        result = {'code': 200}

        ids = request.get_json()
        result['msg'] = f'input task ids: {ids}, remove success ids:'
        for task_id in ids:
            task_id = str(task_id)

            if task_id in engine.task_dict.keys():
                gd.remove_push_stream_pipe(task_id)
                result['msg'] = f'{result["msg"]} {task_id}'

        return result 
    except Exception as e:
        logger.error(str(e))
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
                bboxes, kpss = engine.scrfd.detect(img, args.face_detec_thres1)
                logger.info(f'face num in {img_url} is {len(bboxes)}')

                for bbox, kps in zip(bboxes, kpss):
                    face = norm_crop(img, kps)

                    features, norms = engine.face_recog.get_features([face])
                    name, conf = engine.face_recog.top1(features[0])

                    face_info = {}
                    face_info['name'] = name
                    face_info['conf'] = conf
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
            elif face_name in engine.face_database.keys():
                result['code'] = -2
                result['msg'] = f'face name {face_name} already in face database'
            else:
                bboxes, kpss = engine.scrfd.detect(img, args.face_detec_thres1)
                logger.info(f'face num in {face_name} is {len(bboxes)} ------')

                if len(bboxes) ==  1:
                    face = norm_crop(img, kpss[0])
                    feature = engine.face_recog.get_features([face])[0]

                    engine.face_database.set(face_name, feature)

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

            result['face_list'] = list(engine.face_database.keys())
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

        if face_name not in engine.face_database.keys():
            result['code'] = -1
            result['msg'] = f'face_name {face_name} not in face list'
        else:
            engine.face_database.delete(face_name)

        result['face_list'] = list(engine.face_database.keys())
        return result
    except Exception as e:
        logger.error(str(e))
        return {'code': 500, 'msg': str(e)}


@app.route('/get_face_list', methods=['POST'])
def get_face_list():
    logger.info('get face list ====>')
    return {'code': 200, 'face_list': list(engine.face_database.keys())}


def get_args():
    parser = argparse.ArgumentParser(description='server args')
    parser.add_argument('--triton_port', type=int, default=8000)
    parser.add_argument('--face_detec_model_name', type=str, default='ensemble_scrfd')
    parser.add_argument('--face_recog_model_name', type=str, default='face_recog')
    parser.add_argument('--face_detec_thres1', type=float, default=0.6)
    parser.add_argument('--face_detec_thres2', type=float, default=0.8)
    parser.add_argument('--redis_port', type=int, default=6379)
    parser.add_argument('--face_database_thres', type=float, default=0.35)
    parser.add_argument('--rtmp_server_uri', type=str, default='rtmp://10.0.109.88:1935/live/frtask')

    return parser.parse_args()


if __name__ == '__main__':
    args = get_args()
    logger = get_logger('./logs')
    engine = Engine(logger, args)

    logger.info('start run server ------')
    app.run(host='0.0.0.0',port=5000)
