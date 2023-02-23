import time
import cv2
from src.face_align import norm_crop, transform
from src.utils import convert_image_2_base64_str, drawImg 

def post_process(img_bgr, 
                 logger, 
                 task_id, 
                 scrfd, 
                 sort, 
                 face_recog, 
                 grpc, 
                 pipe, 
                 lastt_dict,
                 global_info):
    t0 = time.time()
    img_bgr = cv2.resize(img_bgr, (1920, 1080))

    t1 = time.time() 
    bboxes, kpss = scrfd.detect(img_bgr, global_info['face_detec_thres2'])
    t2 = time.time() 

    track_outputs = sort.update(bboxes)

    t3 = time.time()

    result_details = dict()
    result_details['behaviorBeginTime'] = int(t3*1000)-30*1000
    result_details['behaviorEndTime'] = int(t3*1000)
    result_details['face_data'] = []
    result_details['msg'] = ''

    image_name_changed = False 
    new_face_list = []

    for (output, bbox, kps) in zip(track_outputs, bboxes, kpss):      
        if output[5] % 5:
            continue

        face = norm_crop(img_bgr, kps)

        features = face_recog.get_features([face])
        top1 = face_recog.top1(features[0])
        
        face_info = {}

        name_changed, face_changed = sort.update_face_info(output[4], top1[0], top1[1], features[0])
        if name_changed:
            face_info['new_face'] = True
            image_name_changed = True
            new_face_list.append(top1[0])
            result_details['msg'] = f'{result_details["msg"]} {top1[0]}'
        else:
            face_info['new_face'] = False 
        
        face_info['name'] = top1[0]
        face_info['conf'] = top1[1] 
        face_info['base64_str'] = convert_image_2_base64_str(face) 
        face_info['bbox'] = bbox.tolist()
        result_details['face_data'].append(face_info)

        logger.info(f'task id: {task_id}, top1 dist: {top1[0]}, {top1[1]} ---')

    t4 = time.time() 

    img_bgr2 = img_bgr.copy()
    if (grpc is not None) and image_name_changed:
        box_arr = []
        text_arr = []
        color_arr = []

        for face_info in result_details['face_data']:
            box = [int(b) for b in face_info['bbox']]
            box_arr.append(box)

            text_arr.append(f'{face_info["name"]}:{face_info["conf"]:.2f}')
            
            color = (0, 0, 255) if face_info['new_face'] else (0, 255, 255)
            color_arr.append(color)

        img_bgr = drawImg(img_bgr, box_arr, text_arr, color_arr, text_size=40)
        result_details['image'] = convert_image_2_base64_str(img_bgr)
        result_details['msg'] = f'{result_details["msg"]} 经过'

        try:
            grpc.send_result(result_details)
        except Exception as e:
            logger.error(f'grpc error: {e}')

    if pipe is not None:
        box_arr = []
        text_arr = []
        color_arr = []

        outputs = sort.get_all()
        for output in outputs:
            box = [int(b) for b in output[:4]]
            box_arr.append(box)
            
            text_arr.append(f'{output[6]}:{output[7]:.2f}')
            
            color = (0, 255, 255)
            color_arr.append(color)

        img_bgr2 = drawImg(img_bgr2, box_arr, text_arr, color_arr, text_size=40)
        try:
            pipe.stdin.write(img_bgr2.tobytes())
        except Exception as e:
            logger.error(f'rtmp error: {e}')

    t5 = time.time()

    cost = t5 - lastt_dict[task_id]
    lastt_dict[task_id] = t5

    if len(bboxes):
        logger.info(f'task id: {task_id}, face num {len(bboxes)}, detec {(t2-t1)*1000:.1f}ms, recog {(t4-t3)*1000:.1f}ms, grpc_rtmp {(t5-t4)*1000:.1f}ms, \
            post {(t5-t0)*1000:.1f}ms, cost {cost*1000:.1f}ms, fps {1.0/cost:.2f} ------')
