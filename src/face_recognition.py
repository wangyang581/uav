import numpy as np
import tritonclient.http as httpclient 

from src.face_database import FaceDatabase 

class FaceRecog:
    def __init__(self, triton_port=8000, redis_port=7999, face_thres=0.35, model_name='face_recog'):
        triton_host = '127.0.0.1:{}'.format(triton_port)
        self.client = httpclient.InferenceServerClient(triton_host)
        self.model_name = model_name 

        # Health check
        # if not self.client.is_server_live():
        #     raise Exception('face recog client failed: is_server_live')
        # if not self.client.is_server_ready():
        #     raise Exception('face recog client failed: is_server_ready')
        # if not self.client.is_model_ready(self.model_name):
        #     raise Exception('face recog client failed: is_model_ready')

        self.input_name = 'input'
        self.output_names = ['features', 'norms']

        self.inputs = [httpclient.InferInput(self.input_name, [1, 3, 112, 112], 'FP32')]
        self.outputs = [httpclient.InferRequestedOutput(name) for name in self.output_names]
        self.face_database = FaceDatabase(redis_port, face_thres)

    def get_features(self, faces_bgr):
        faces_np = np.array(faces_bgr, dtype=np.float32)
        blob = ((faces_np / 255.) - 0.5) / 0.5
        blob = blob.transpose(0, 3, 1, 2)

        self.inputs[0].set_data_from_numpy(blob)

        response = self.client.infer(self.model_name,
                                     self.inputs,
                                     request_id=str(1),
                                     outputs=self.outputs)

        # result = response.get_response()

        features, norms = [response.as_numpy(name) for name in self.output_names]

        return features, norms

    def top1(self, feature, add_stranger=0):
        return self.face_database.top1(feature, add_stranger)