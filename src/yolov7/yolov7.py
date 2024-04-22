#!/usr/bin/env python

import argparse
import numpy as np
import sys
import cv2
import time

import tritonclient.grpc as grpcclient
from tritonclient.utils import InferenceServerException

from .processing import preprocess, postprocess
from src.render import render_box, render_filled_box, get_text_size, render_text, RAND_COLORS
from .labels import COCOLabels

INPUT_NAMES = ["images"]
OUTPUT_NAMES = ["num_dets", "det_boxes", "det_scores", "det_classes"]

def yolov7_triton():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode',
                        choices=['dummy', 'image', 'video'],
                        default='image',
                        help='Run mode. \'dummy\' will send an emtpy buffer to the server to test if inference works. \'image\' will process an image. \'video\' will process a video.')
    parser.add_argument('--input',
                        type=str,
                        nargs='?',
                        help='Input file to load from in image or video mode')
    parser.add_argument('-m',
                        '--model',
                        type=str,
                        required=False,
                        default='ensemble_yolov7',
                        help='Inference model name, default yolov7')
    parser.add_argument('--width',
                        type=int,
                        required=False,
                        default=640,
                        help='Inference model input width, default 640')
    parser.add_argument('--height',
                        type=int,
                        required=False,
                        default=640,
                        help='Inference model input height, default 640')
    parser.add_argument('-u',
                        '--url',
                        type=str,
                        required=False,
                        default='localhost:8001',
                        help='Inference server URL, default localhost:8001')
    parser.add_argument('-o',
                        '--out',
                        type=str,
                        required=False,
                        default='',
                        help='Write output into file instead of displaying it')
    parser.add_argument('-f',
                        '--fps',
                        type=float,
                        required=False,
                        default=24.0,
                        help='Video output fps, default 24.0 FPS')
    parser.add_argument('-i',
                        '--model-info',
                        action="store_true",
                        required=False,
                        default=False,
                        help='Print model status, configuration and statistics')
    parser.add_argument('-v',
                        '--verbose',
                        action="store_true",
                        required=False,
                        default=False,
                        help='Enable verbose client output')
    parser.add_argument('-t',
                        '--client-timeout',
                        type=float,
                        required=False,
                        default=None,
                        help='Client timeout in seconds, default no timeout')
    parser.add_argument('-s',
                        '--ssl',
                        action="store_true",
                        required=False,
                        default=False,
                        help='Enable SSL encrypted channel to the server')
    parser.add_argument('-r',
                        '--root-certificates',
                        type=str,
                        required=False,
                        default=None,
                        help='File holding PEM-encoded root certificates, default none')
    parser.add_argument('-p',
                        '--private-key',
                        type=str,
                        required=False,
                        default=None,
                        help='File holding PEM-encoded private key, default is none')
    parser.add_argument('-x',
                        '--certificate-chain',
                        type=str,
                        required=False,
                        default=None,
                        help='File holding PEM-encoded certicate chain default is none')

    FLAGS = parser.parse_args()

    # Create server context
    

    try:
        triton_client = grpcclient.InferenceServerClient(
            url=FLAGS.url,
            verbose=FLAGS.verbose,
            ssl=FLAGS.ssl,
            root_certificates=FLAGS.root_certificates,
            private_key=FLAGS.private_key,
            certificate_chain=FLAGS.certificate_chain)
    except Exception as e:
        print("context creation failed: " + str(e))
        sys.exit()
    
    t111 = time.time()
    # Health check
    if not triton_client.is_server_live():
        print("FAILED : is_server_live")
        sys.exit(1)

    if not triton_client.is_server_ready():
        print("FAILED : is_server_ready")
        sys.exit(1)

    # if not triton_client.is_model_ready(FLAGS.model):
    #     print("FAILED : is_model_ready")
    #     sys.exit(1)

    print('ssss',time.time()-t111)
    


    t0=time.time() 



    return triton_client

def yolov7_detect(img_bgr,triton_client,size,model):

    inputs = []
    outputs = []
    # inputs.append(grpcclient.InferInput(INPUT_NAMES[0], [1, 3, FLAGS.width, FLAGS.height], "FP32"))
    inputs.append(grpcclient.InferInput(INPUT_NAMES[0], [1,  size[0], size[1],3], "UINT8"))
    outputs.append(grpcclient.InferRequestedOutput(OUTPUT_NAMES[0]))
    outputs.append(grpcclient.InferRequestedOutput(OUTPUT_NAMES[1]))
    outputs.append(grpcclient.InferRequestedOutput(OUTPUT_NAMES[2]))
    outputs.append(grpcclient.InferRequestedOutput(OUTPUT_NAMES[3]))
    # print("Creating buffer from image file...")
    input_image = img_bgr
    if input_image is None:
        print("could not load input image")
        sys.exit(1)

    t1 = time.time()

    input_image_buffer = preprocess(input_image, size)


    input_image_buffer = np.expand_dims(input_image_buffer, axis=0)
    
    inputs[0].set_data_from_numpy(input_image_buffer)
    t2=time.time()
    print('pre',t2-t1)


    # print("Invoking inference...")

    t21 = time.time()
    results = triton_client.infer(model_name=model,
                                    inputs=inputs,
                                    outputs=outputs,
                                    client_timeout=None)

    t22 = time.time()
    print('inf',t22-t21)

    t31 = time.time()
    num_dets = results.as_numpy(OUTPUT_NAMES[0])
    det_boxes = results.as_numpy(OUTPUT_NAMES[1])
    det_scores = results.as_numpy(OUTPUT_NAMES[2])
    det_classes = results.as_numpy(OUTPUT_NAMES[3])
    detected_objects = postprocess(num_dets, det_boxes, det_scores, det_classes, input_image.shape[1], input_image.shape[0], size)
    #print(f"Detected objects: {len(detected_objects)}")
    t32 = time.time()
    print('post',t32-t31)

    return detected_objects

