import grpc
import json

import src.grpc_py.inference_result_pb2 as pb2
import src.grpc_py.inference_result_pb2_grpc as pb2_grpc

class GrpcClient:
    def __init__(self, address, task_id):
        self.address = address
        self.task_id = str(task_id)

        channel = grpc.insecure_channel(address)
        self.stub = pb2_grpc.InferenceCallbackServiceStub(channel)
        self.request = pb2.InferenceCallbackRequest

    def send_result(self, analysis_result):
        request_curr = self.request(
            task_id=self.task_id,
            analysis_result=json.dumps(analysis_result),
            result_type='1',
            callback_type='1'
            )
        response = self.stub.checkpoint(request_curr)
        return response
