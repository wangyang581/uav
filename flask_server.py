from flask import Flask, request 
import json 
import cv2
import argparse

from src.engine_opencv import Engine 

from src.utils import get_logger, convert_image_2_base64_str
from src.grpc_client import GrpcClient
from src.global_dict import gd
import threading
import ast

app = Flask(__name__)

@app.route('/add_source', methods=['POST'])
def add_source():
    logger.info('add source ====>')
    try:
        logger.info(f'input: {request.form}')
        result = {'code': 200}
        result['msg'] = 'add source success.'

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
        result['msg'] = 'remove_source'

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


@app.route('/rebuild_source', methods=['POST'],endpoint="rebuild_source")
def rebuild_source():
    logger.info('rebuild source ====>')
    try:
        logger.info(f'input: {request.form}')
        result = {'code': 200}

        result['msg'] = 'rebuild_source'

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


@app.route('/source_status', methods=['POST'],endpoint="source_status")
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
    

@app.route('/source_status/all', methods=['GET'],endpoint="source_status_all")
def source_status_all():
    logger.info('source_status_all ====>')

    result = dict()
    for task_id in gd.heart_beat_dict.keys():

        heart_beat = gd.heart_beat_dict.get(task_id) 
        if heart_beat is not None:
                result[task_id] = heart_beat.is_alive()
        else:
            result[task_id] = False

    return {'code': 200, 'data': json.dumps(result)}


@app.route('/update_source', methods=['PUT'],endpoint="update_source")
def update_source():
    logger.info('update source ====>')
    try:
        logger.info(f'input: {request.form}')
        result = {'code': 200}
        result['msg'] = 'update_source'

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
        result['msg'] = 'remove_push_stream_pipe'

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
    


def get_args():
    parser = argparse.ArgumentParser(description='server args')
    parser.add_argument('--triton_port', type=int, default=8000)

    parser.add_argument('--rtmp_server_uri', type=str, default='rtmp://10.0.107.111:1935/live/')

    return parser.parse_args()


if __name__ == '__main__':
    args = get_args()
    logger = get_logger('./logs')
    model_lock = threading.Lock()
    model_lock_1 = threading.Lock()

    engine = Engine(logger, args, model_lock, model_lock_1)

    logger.info('start run server ------')
    app.run(host='0.0.0.0',port=5000)
