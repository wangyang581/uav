import time
from src.face_align import norm_crop 
from src.utils import convert_image_2_base64_str, drawImg 
from src.global_dict import gd

def post_process(img_bgr, task_id, args, logger, scrfd, sort, face_recog):
    t1 = time.time() 
    bboxes, kpss = scrfd.detect(img_bgr, args.face_detec_thres2)
    t2 = time.time() 

    track_outputs = sort.update(bboxes)
    t3 = time.time()

    result_details = dict()
    result_details['behaviorBeginTime'] = int(t3*1000)-30*1000
    result_details['behaviorEndTime'] = int(t3*1000)
    result_details['face_data'] = []
    result_details['msg'] = ''

    image_name_changed = False 
    add_stranger = gd.rule_info_dict[task_id].get('add_stranger', 0)
    alert_time = gd.rule_info_dict[task_id].get('alert_time', '60')
    alert_time = int(alert_time)

    for (output, bbox, kps) in zip(track_outputs, bboxes, kpss):      
        if output[5] % 5:
            continue

        face_bgr = norm_crop(img_bgr, kps)

        features, norms = face_recog.get_features([face_bgr])
        name, conf = face_recog.top1(features[0], add_stranger)
        
        face_info = {}

        name_changed = sort.update_face_info(output[4], name, conf)
        if name_changed:
            face_info['new_face'] = True
            image_name_changed = True
        else:
            face_info['new_face'] = False 
        
        face_info['task_id'] = task_id
        face_info['name'] = name
        face_info['conf'] = conf
        face_info['base64_str'] = convert_image_2_base64_str(face_bgr) 
        face_info['bbox'] = bbox.tolist()
        result_details['face_data'].append(face_info)

        logger.info(f'task id: {task_id}, top1 conf: {name}, {conf:.4f} ---')

    t4 = time.time() 

    img_bgr2 = img_bgr.copy()
    if (gd.grpc_dict[task_id] is not None) and image_name_changed:
        box_arr = []
        text_arr = []
        color_arr = []
        alert_name_arr = []

        for face_info in result_details['face_data']:
            name = face_info['name']
            last_time = gd.alert_dict[task_id].get(name, t4 - alert_time)
            if t4 - last_time < alert_time:
                continue
            else:
                gd.alert_dict[task_id][name] = t4

            box = [int(b) for b in face_info['bbox']]
            box_arr.append(box)

            text_arr.append(f'{face_info["name"]}:{face_info["conf"]:.2f}')
            
            color = (0, 0, 255) if face_info['new_face'] else (0, 255, 255)
            color_arr.append(color)

            if face_info['new_face']: 
                result_details['msg'] = f'{result_details["msg"]} {name}'
                alert_name_arr.append(name)

        if len(alert_name_arr):
            img_bgr = drawImg(img_bgr, box_arr, text_arr, color_arr, text_size=40)
            result_details['image'] = convert_image_2_base64_str(img_bgr)
            result_details['msg'] = f'{result_details["msg"]} 经过'

            try:
                gd.grpc_dict[task_id].send_result(result_details)
            except Exception as e:
                logger.error(f'grpc error: {e}')

    if gd.pipe_dict[task_id] is not None:
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
            gd.pipe_dict[task_id].stdin.write(img_bgr2.tobytes())
        except Exception as e:
            logger.error(f'rtmp error: {e}')

    t5 = time.time()

    cost = t5 - gd.lastt_dict[task_id]
    gd.lastt_dict[task_id] = t5

    if len(bboxes):
        logger.info(f'task id: {task_id}, face num {len(bboxes)}, detec {(t2-t1)*1000:.1f}ms, recog {(t4-t3)*1000:.1f}ms, grpc_rtmp {(t5-t4)*1000:.1f}ms, post {(t5-t1)*1000:.1f}ms, cost {cost*1000:.1f}ms, fps {1.0/cost:.2f} ------')
