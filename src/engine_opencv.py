from src.utils import get_logger 
from src.sort.sort import Sort
from src.stream_factory import StreamFactory
from src.grpc_client import GrpcClient

from threading import Thread 
import queue

import cv2 

from src.scrfd import SCRFD 
from src.face_recognition import FaceRecog 

from src.post_process import post_process

class Engine:
    def __init__(self,
                 logger,
                 global_info):
        self.task_dict = {}
        self.cam_dict = {}

        self.logger = logger
        self.global_info = global_info

        self.logger_dict = {}
        self.sort_dict = {}
        self.grpc_dict = {}
        self.pipe_dict = {}
        self.lastt_dict = {}        

        self.logger.info('engine inited ------') 

    def add_source(self, uri_name, task_id, grpc_address, rtmp_address, stream_frequency, heart_beat):
        if task_id not in self.logger_dict.keys():
            self.logger_dict[task_id] = get_logger('./logs', f'{task_id}.log')

        self.sort_dict[task_id] = Sort()
        self.lastt_dict[task_id] = 0

        self.grpc_dict[task_id] = GrpcClient(grpc_address, task_id) if grpc_address else None
        self.pipe_dict[task_id] = StreamFactory.new_pipe(stream_frequency, rtmp_address) if rtmp_address else None

        self.logger.info(f'creating video capture task {uri_name} ------')
        self.cam_dict[task_id] = VideoCapture(uri_name, self.logger)
        self.cam_dict[task_id].start()

        self.logger.info(f'creating stream task {task_id} ------')
        self.task_dict[task_id] = StreamTask(self.cam_dict, task_id, self.logger_dict, self.sort_dict, \
            self.grpc_dict, self.pipe_dict, self.lastt_dict, stream_frequency, heart_beat, self.global_info)
        self.task_dict[task_id].start()
    
    def remove_source(self, task_id):
        if task_id not in self.task_dict.keys():
            self.logger.info(f'no task_id {task_id} ------')
            return False 

        self.cam_dict[task_id].stop()
        self.cam_dict.pop(task_id)
        
        self.task_dict.pop(task_id)

        self.sort_dict.pop(task_id)
        self.lastt_dict.pop(task_id)

        self.grpc_dict.pop(task_id)
        if self.pipe_dict[task_id] is not None:
            self.pipe_dict[task_id].kill()
        self.pipe_dict.pop(task_id)

        return True         

class VideoCapture(Thread):
    def __init__(self, name, logger, mode='gpu'):
        super(VideoCapture, self).__init__()
        self.mode = mode 
        self.name = name

        if self.mode == 'cpu':
            self.cap = cv2.VideoCapture(name)
        elif self.mode == 'gpu':
            self.cap = cv2.cudacodec.createVideoReader(name)
        else:
            raise

        self.stopped = False
        self.logger = logger
        self.q = queue.Queue()

    # read frames as soon as they are available, keeping only most recent one
    def run(self):
        self.logger.info(f'videocapture {self.name} start ------')
        while not self.stopped:
            if self.mode == 'cpu':
                ret, frame = self.cap.read()
            elif self.mode == 'gpu':
                ret, frame = self.cap.nextFrame()
            else:
                raise

            if not ret:
                break
            if not self.q.empty():
                try:
                    self.q.get_nowait()   # discard previous (unprocessed) frame
                except queue.Empty:
                    pass
            self.q.put(frame)

        if self.mode == 'cpu':
            self.cap.release()
        self.stopped = True 
        self.logger.error(f'video capture {self.name} break ------')

    def stop(self):
        if self.mode == 'cpu':
            self.cap.release()
        self.stopped = True
        self.logger.info(f'stop video capture {self.name}------')

    def read(self):
        frame = self.q.get()
        if self.mode == 'gpu':
            frame = frame.download()
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

        return frame

class StreamTask(Thread):
    def __init__(self, 
                 cam_dict, 
                 task_id, 
                 logger_dict, 
                 sort_dict, 
                 grpc_dict, 
                 pipe_dict, 
                 lastt_dict,
                 stream_frequency,
                 heart_beat,
                 global_info):
        super(StreamTask, self).__init__()

        self.task_id = task_id 

        self.logger = logger_dict[task_id]
        self.sort = sort_dict[task_id]
        self.grpc = grpc_dict.get(task_id, None)
        self.pipe = pipe_dict.get(task_id, None)
        self.lastt_dict = lastt_dict

        self.stream_frequency = stream_frequency
        self.heart_beat = heart_beat

        self.scrfd = SCRFD(global_info['triton_host'], global_info['face_detec_model_name']) 
        self.face_recog = FaceRecog(global_info['triton_host'], global_info['face_recog_model_name'])

        self.cam = cam_dict[task_id]
        self.global_info = global_info

        self.frame_count = 0

    def run(self):
        self.logger.info(f'stream task {self.task_id} start ------')
        while not self.cam.stopped:
            img = self.cam.read() 
            if img is None:
                break

            # self.frame_count += 1
            # if self.frame_count % self.stream_frequency == 0:
            #     self.heart_beat.beat()
            self.heart_beat.beat()

            post_process(img, self.logger, self.task_id, self.scrfd, self.sort, self.face_recog, \
                         self.grpc, self.pipe, self.lastt_dict, self.global_info)
        self.logger.info(f'stream task {self.task_id} break ------')
