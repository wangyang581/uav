import time 

from src.utils import get_logger, HeartBeat
from src.stream_factory import StreamFactory
from src.grpc_client import GrpcClient

global gd 

class GlobalDict():
    def __init__(self):
        self.logger_dict = {}

        self.lastt_dict = {}
        self.alert_dict = {}
        self.rule_info_dict = {}

        self.grpc_dict = {}
        self.pipe_dict = {}
        self.stream_frequency_dict = {}
        self.rtmp_server_uri = ''

        self.heart_beat_dict = {}

    def add_task(self, task_id, grpc_address, stream_frequency, rule_info):
        if task_id not in self.logger_dict.keys():
            self.logger_dict[task_id] = get_logger('./logs', f'{task_id}.log')

        self.lastt_dict[task_id] = time.time()
        self.alert_dict[task_id] = {}
        self.rule_info_dict[task_id] = rule_info

        self.grpc_dict[task_id] = GrpcClient(grpc_address, task_id) if grpc_address else None
        self.pipe_dict[task_id] = None
        self.stream_frequency_dict[task_id] = stream_frequency 

        self.heart_beat_dict[task_id] = HeartBeat(task_id)

    def remove_task(self, task_id):
        if task_id in self.lastt_dict.keys(): self.lastt_dict.pop(task_id)
        if task_id in self.alert_dict.keys(): self.alert_dict.pop(task_id)
        if task_id in self.rule_info_dict.keys(): self.rule_info_dict.pop(task_id)
        
        if task_id in self.grpc_dict.keys(): self.grpc_dict.pop(task_id)
        if task_id in self.pipe_dict.keys():
            if self.pipe_dict[task_id]:
                self.pipe_dict[task_id].kill()
            self.pipe_dict.pop(task_id)
        if task_id in self.stream_frequency_dict.keys():
            self.stream_frequency_dict.pop(task_id)

        if task_id in self.heart_beat_dict.keys(): self.heart_beat_dict.pop(task_id)

    def update_task(self, task_id, grpc_address, stream_frequency, rule_info):
        if task_id in self.rule_info_dict.keys():
            self.rule_info_dict[task_id] = rule_info 
        
    def create_push_stream_pipe(self, task_id, rtmp_server_uri):
        if task_id in self.pipe_dict.keys():
            if self.pipe_dict[task_id]:
                self.pipe_dict[task_id].kill()

            stream_frequency = self.stream_frequency_dict.get(task_id, 25)
            self.pipe_dict[task_id] = StreamFactory.new_pipe(stream_frequency, f'{rtmp_server_uri}_{task_id}')

    def remove_push_stream_pipe(self, task_id):
        if task_id in self.pipe_dict.keys():
            if self.pipe_dict[task_id]:
                self.pipe_dict[task_id].kill()
            
            self.pipe_dict[task_id] = None

gd = GlobalDict()
