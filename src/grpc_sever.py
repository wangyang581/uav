from concurrent import futures
import time
import datetime
import grpc

import sys
import os
path = os.path.dirname(__file__)
sys.path.append(path)

import src.grpc_py.inference_result_pb2 as pb2
import src.grpc_py.inference_result_pb2_grpc as pb2_grpc

import base64
import numpy as np
import cv2 
from PIL import Image 
import json

class InferenceCallbackService(pb2_grpc.InferenceCallbackService):
    def checkpoint(self, request, context):
        task_id = request.task_id
        result = request.analysis_result
        result = json.loads(result)

        print('task id:', task_id, ',', result['msg'])
        t = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        t1 = result['behaviorBeginTime']
        t2 = result['behaviorEndTime']
        image_data = result.get('image', None)

        if image_data is not None:
            save_name = f'./grpc_images/frame_images/taskid{task_id}_{t}.jpg'
            image_data_b = base64.b64decode(image_data)
            pil_image = Image.frombuffer('RGB', (1920, 1080), image_data_b, 'jpeg', 'RGB', None)
            cv_image = np.asarray(pil_image)
            cv2.imwrite(save_name, cv_image[:,:,::-1])

            print(f'{t}, image saved to {save_name}')

        for face_info in result['face_data']:
            base64_str = face_info['base64_str']
            name = face_info['name']
            conf = face_info['conf']
            task_id = face_info['task_id']

            save_name = f'./grpc_images/face_images/taskid{task_id}_{t}_{name}_{conf:.2f}_{face_info["new_face"]}.jpg'
            face_data_b = base64.b64decode(base64_str)
            pil_face = Image.frombuffer('RGB', (112, 112), face_data_b, 'jpeg', 'RGB', None)
            cv_face = np.asarray(pil_face)
            cv2.imwrite(save_name, cv_face[:,:,::-1])

            print(f'{t}, face saved to {save_name}')

        return pb2.InferenceCallbackResponse(code=int(request.task_id), msg=str(request.analysis_result))

def serve():
    os.makedirs('./grpc_images/frame_images', exist_ok=True)
    os.makedirs('./grpc_images/face_images', exist_ok=True)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pb2_grpc.add_InferenceCallbackServiceServicer_to_server(InferenceCallbackService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print('server started ------')

    try:
        while True:
            time.sleep(60*60*24)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    serve()
