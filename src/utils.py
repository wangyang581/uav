import sys
import os
import logging, logging.handlers

import base64
from PIL import Image, ImageFont, ImageDraw 
from io import BytesIO

import numpy as np
import cv2
import time 

file_path = os.path.abspath(__file__)
file_path_arr = os.path.split(file_path)
font_path = os.path.join(file_path_arr[0], 'simsun.ttc')

def get_logger(log_dir, log_file='log.txt'):
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    filename = os.path.join(log_dir, log_file)
    log_format = '%(asctime)s %(message)s'

    logger = logging.getLogger(log_file.split('.')[0])
    logger.setLevel(level=logging.INFO)

    # file_handler = logging.FileHandler(filename)
    file_handler = logging.handlers.RotatingFileHandler(filename, maxBytes=100*1024*1024, backupCount=9)
    file_handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(file_handler)    

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(stream_handler)

    return logger

def convert_image_2_base64_str(image,format='JPEG'):
    img=Image.fromarray(image[:,:,::-1])
    output_buffer = BytesIO()
    img=img.convert('RGB')
    img.save(output_buffer, format=format)
    byte_data = output_buffer.getvalue()
    return base64.b64encode(byte_data).decode('utf-8')

def drawImg(img_opencv, box_arr, text_arr, color_arr, text_size=20):
    for box, color in zip(box_arr, color_arr):
        cv2.rectangle(img_opencv, box[0:2], box[2:4], color, 2)

    img_pil = Image.fromarray(img_opencv)
    font = ImageFont.truetype(font_path, text_size)

    draw = ImageDraw.Draw(img_pil)
    for box, text, color in zip(box_arr, text_arr, color_arr):
        if not isinstance(text, np.unicode):
            text = text.decode('utf8')
        draw.text((box[0], box[1]-text_size), text, font=font, fill=color)
    return np.asarray(img_pil)

class HeartBeat():
    def __init__(self, id, threshold=1*60):
        self.id = id 
        self.threshold = threshold 
        self.last_beat = int(time.time())

    def is_alive(self):
        now = int(time.time())
        return now - self.last_beat < self.threshold

    def beat(self):
        self.last_beat = int(time.time())

class AverageMeter():
    def __init__(self, len=100):
        self.val = 0
        self.sum = 0
        self.avg = 0
        self.count = 0

        self.len = len
        self.arr = []

    def update(self, val):
        self.val = val
        self.sum += val
        self.count += 1

        if self.len > 0:
            self.arr.append(val)
            if len(self.arr) > self.len:
                self.sum -= self.arr[0]
                self.arr.pop(0)
                self.count -= 1

        self.avg = self.sum / self.count
