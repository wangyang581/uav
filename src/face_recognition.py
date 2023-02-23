import numpy as np
import tritonclient.http as httpclient 

from src.face_database import FaceDatabase 

class FaceRecog:
    def __init__(self, triton_host='localhost:8000', model_name='face_recog'):
        self.client = httpclient.InferenceServerClient(triton_host)
        self.model_name = model_name 

        self.input_name = 'input'
        self.output_name = 'output'

        self.inputs = [httpclient.InferInput(self.input_name, [1, 3, 112, 112], 'FP32')]
        self.outputs = [httpclient.InferRequestedOutput(self.output_name)]
        self.face_database = FaceDatabase('127.0.0.1', 7999, 0.35)

    def get_features(self, faces):
        faces_np = np.array(faces, dtype=np.float32)
        blob = ((faces_np[:,:,::-1] / 255.) - 0.5) / 0.5
        blob = blob.transpose(0, 3, 1, 2)

        self.inputs[0].set_data_from_numpy(blob)

        response = self.client.infer(self.model_name,
                                     self.inputs,
                                     request_id=str(1),
                                     outputs=self.outputs)

        result = response.get_response()

        features = response.as_numpy(self.output_name)

        return features

    def top1(self, feature):
        return self.face_database.top1(feature)