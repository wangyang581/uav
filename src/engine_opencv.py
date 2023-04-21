from threading import Thread 
import queue
import time 

import cv2 

from src.scrfd import SCRFD 
from src.face_recognition import FaceRecog 
from src.sort.sort import Sort
from src.face_database import FaceDatabase
from src.post_process import post_process
from src.global_dict import gd

class Engine:
    def __init__(self, logger, args):
        self.logger = logger
        self.args = args

        self.cam_dict = {}
        self.task_dict = {}

        self.face_database = FaceDatabase(args.redis_port, args.face_database_thres)
        self.scrfd = SCRFD(args.triton_port, args.face_detec_model_name) 
        self.face_recog = FaceRecog(args.triton_port, args.redis_port, args.face_database_thres, args.face_recog_model_name)

        self.logger.info('engine inited ------') 

    def add_source(self, task_id, stream_url, grpc_address, stream_frequency, rule_info):
        gd.add_task(task_id, grpc_address, stream_frequency, rule_info)

        decode_mode = rule_info = rule_info.get('mode', 'cpu')
        decode_mode = str(decode_mode)

        self.logger.info(f'creating video capture task {stream_url} ------')
        self.cam_dict[task_id] = VideoCapture(task_id, stream_url, self.logger, mode=decode_mode)
        self.cam_dict[task_id].start()

        self.logger.info(f'creating stream task {task_id} ------')
        self.task_dict[task_id] = StreamTask(task_id, self.args, self.cam_dict)
        self.task_dict[task_id].start()
    
    def remove_source(self, task_id):
        if task_id in self.cam_dict.keys():
            self.cam_dict[task_id].stop()
            self.cam_dict.pop(task_id)

        self.task_dict.pop(task_id)
        gd.remove_task(task_id)        
    

class VideoCapture(Thread):
    def __init__(self, task_id, stream_url, logger, mode='cpu'):
        super(VideoCapture, self).__init__() 
        self.task_id = task_id
        self.stream_url = stream_url
        self.mode = mode

        if self.mode == 'cpu':
            self.cap = cv2.VideoCapture(stream_url)
        elif self.mode == 'gpu':
            self.cap = cv2.cudacodec.createVideoReader(stream_url)
        else:
            raise Exception(f'do not support such mode {self.mode}')

        self.stopped = False
        self.logger = logger
        self.q = queue.Queue()

        self.frame_count = 0

    # read frames as soon as they are available, keeping only most recent one
    def run(self):
        self.logger.info(f'videocapture task_id {self.task_id} stream_url {self.stream_url} start ------')
        while not self.stopped:
            try:
                if self.mode == 'cpu':
                    ret, frame = self.cap.read()
                    if not ret: break
                    frame = cv2.resize(frame, (1920, 1080))
                else :
                    ret, frame = self.cap.nextFrame()
                    if not ret: break 
                    frame = cv2.cuda.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                    frame = cv2.cuda.resize(frame, (1920, 1080))
                    frame = frame.download()
            except Exception as e:
                self.logger.error(f'stream read errer: {e} ------')
                break

            skip_rate = gd.rule_info_dict[self.task_id].get('skip_frame_rate', 0)

            if skip_rate <= 0:
                if not self.q.empty():
                    try:
                        self.q.get_nowait()   # discard previous (unprocessed) frame
                    except queue.Empty:
                        pass 
                self.q.put(frame)
            elif self.frame_count % skip_rate == 0:
                if self.q.qsize() >= 50:
                    self.q.queue.clear()
                self.q.put(frame)

            self.frame_count += 1

        self.q.queue.clear()
        if self.mode == 'cpu':
            self.cap.release()

        self.stopped = True
        self.logger.info(f'videocapture task_id {self.task_id} stream_url {self.stream_url} stopped ------')

    def stop(self):
        self.stopped = True
        self.logger.info(f'stopping videocapture task_id {self.task_id} stream_url {self.stream_url}------')

    def read(self):
        if self.stopped: return None 

        frame = self.q.get()
        return frame

class StreamTask(Thread):
    def __init__(self, task_id, args, cam_dict):
        super(StreamTask, self).__init__()

        self.task_id = task_id 
        self.args = args 
        self.cam = cam_dict[task_id]

        self.logger = gd.logger_dict[task_id]
        self.frame_count = 0

        self.scrfd = SCRFD(args.triton_port, args.face_detec_model_name) 
        self.face_recog = FaceRecog(args.triton_port, args.redis_port, args.face_database_thres, args.face_recog_model_name)
        self.sort = Sort()

    def run(self):
        self.logger.info(f'stream task {self.task_id} start ------')
        while not self.cam.stopped:
            img = self.cam.read() 
            if img is None:
                self.logger.error('img is none ------')
                break

            self.frame_count += 1
            gd.heart_beat_dict[self.task_id].beat()

            post_process(img, self.task_id, self.args, self.logger, self.scrfd, self.sort, self.face_recog)
        self.logger.info(f'stream task {self.task_id} break ------')
