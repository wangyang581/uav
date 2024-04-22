from threading import Thread 
import queue
import time
import random


import cv2
# from src.sort.sort import Sort
from src.post_process_v8 import post_process_v8
from src.global_dict import gd
# from src.yolov7.yolov7 import yolov7_triton
from ultralytics import YOLO

class Engine:
    def __init__(self, logger, args, model_lock, model_lock_1):
        self.logger = logger
        self.args = args
        self.model_lock = model_lock
        self.model_lock_1 = model_lock_1
        self.cam_dict = {}
        self.task_dict = {}

        self.model_v8 = YOLO('src/ultralytics/weight/last.pt')
       

        self.logger.info('engine inited ------')

        # self.triton_client = yolov7_triton() 

    def add_source(self, task_id, stream_url, grpc_address, stream_frequency, rule_info):
        gd.add_task(task_id, grpc_address, stream_frequency, rule_info)

        decode_mode = rule_info = rule_info.get('mode', 'cpu')
        decode_mode = str(decode_mode)

        self.logger.info(f'creating video capture task {stream_url} ------')
        self.cam_dict[task_id] = VideoCapture(task_id, stream_url, self.logger, mode=decode_mode)
        self.cam_dict[task_id].start()

        self.logger.info(f'creating stream task {task_id} ------')
        self.task_dict[task_id] = StreamTask(task_id, self.args, self.cam_dict, self.model_v8, self.model_lock,self.model_lock_1)
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
            self.cap = cv2.VideoCapture(str(stream_url))
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
            

            skip_rate = gd.rule_info_dict[self.task_id].get('skip_frame_rate', 0)

            if self.mode == 'cpu':
                try:
                    ret = self.cap.grab()
                    if not ret: break
                        
                except Exception as e:
                    self.logger.error(f'stream read errer: {e} ------')
                    break
                if skip_rate <= 0:
                    ret, frame = self.cap.retrieve()
                    frame = cv2.resize(frame, (1920, 1080))
                    if not self.q.empty():
                        try:
                            self.q.get_nowait()   # discard previous (unprocessed) frame
                        except queue.Empty:
                            pass
                    self.q.put(frame)
                elif self.frame_count % skip_rate == 0:

                    ret, frame = self.cap.retrieve()
                    frame = cv2.resize(frame, (1920, 1080))
                    
                    if self.q.qsize() >= 60:
                        self.q.queue.clear()
                    self.q.put(frame)

                self.frame_count += 1


        self.q.queue.clear()
        if self.mode == 'cpu':
            self.cap.release()
        else:
            self.cap.terminate()

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
    def __init__(self, task_id, args, cam_dict, model_v8, model_lock, model_lock_1):
        super(StreamTask, self).__init__()

        self.task_id = task_id
        self.args = args
        self.cam = cam_dict[task_id]

        self.logger = gd.logger_dict[task_id]
        self.frame_count = 0

        self.ocr_img_list = []
        self.id_startTime_list = []
        self.person_result_list = []
        self.box_result_list = []
        self.msg_str_dic = {}


        self.person_in = [0]

        self.model_v8 = model_v8
  
        self.model_lock = model_lock
        self.model_lock_1 = model_lock_1
        
        self.track_history = {}
        self.color = [[random.randint(0, 255) for _ in range(3)] for _ in range(2)]


        
       
    def run(self):
        self.logger.info(f'stream task {self.task_id} start ------')
        while not self.cam.stopped:
            img = self.cam.read() 
            if img is None:
                self.logger.error('img is none ------')
                break

            self.frame_count += 1
            
            gd.heart_beat_dict[self.task_id].beat()

            
            
            post_process_v8(img, self.task_id, self.args, self.logger, self.model_v8,
                            self.frame_count,self.ocr_img_list,self.id_startTime_list,self.person_result_list,
                            self.box_result_list,self.msg_str_dic,self.person_in, self.model_lock, self.model_lock_1, self.track_history, self.color)

        self.logger.info(f'stream task {self.task_id} break ------')
