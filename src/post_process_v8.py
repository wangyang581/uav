import time
from src.utils import convert_image_2_base64_str, drawImg ,draw_roi_box,judge_in,draw_bbox_box,id_in_list,id_in_list_2,id_in_list_3,person_in_list,is_intersect, bbox_iou
from src.global_dict import gd
import cv2

import time
import ast

def post_process_v8(frame_image, task_id, args, logger, model_v8, frame_count,ocr_img_list,id_startTime_list,
                    person_result_list,box_result_list, msg_str_dic,person_in, model_lock, model_lock_1,track_history, color):

    labels_list = ['pedestrian','people','bicycle','car','van',
                    'truck','tricycle','awning-tricycle','bus','motor']
    
    detect_box = {}
    ####行人检测区域获取
    detect_areas = gd.rule_info_dict[task_id].get('detect_areas',[])
    if detect_areas == []:
        detect_areass = [(0, 0), (frame_image.shape[1], 0), (frame_image.shape[1], frame_image.shape[0]),
                        (0, frame_image.shape[0])]
    else:
        detect_areas = ast.literal_eval(detect_areas)
        detect_areass = []
    
        for i in range(len(detect_areas)):
            detect_areass.append((detect_areas[i][0] * 2, detect_areas[i][1] * 2))


    


    ############################################行人检测#####################################################################
    detected_roi_list = [] #存放单帧区域内检测结果(人和包裹)
    img = frame_image[..., ::-1]
    model_lock.acquire()
    # detect_results = model_v8.predict(source=frame_image, imgsz=640, iou=0.7, conf=0.25, verbose=False)
    detect_results = model_v8.track(source=img, imgsz=640, iou=0.7, conf=0.25, verbose=False)
    model_lock.release()

    # annotated_frame = detect_results[0].plot()


    ########################################################################################################################
    # result_list = [] #只存放单帧人类别标签
    for result in detect_results[0]:
        
        xyxy = result.boxes.xyxy.cpu().numpy().tolist()[0]
        # cls = int(result.boxes.cls.cpu().numpy().tolist()[0])
        # conf = result.boxes.conf.cpu().numpy().tolist()[0]
        boxes = result.boxes.xyxy.cpu()
        track_ids = result.boxes.id

        if track_ids is None:
            continue
        else:
            track_ids = track_ids.int().cpu().tolist()
        # annotated_frame = result.orig_img

        for box, track_id in zip(boxes, track_ids):
            if bool(track_history):
                
                if track_id in track_history:
                    iou = bbox_iou(track_history[track_id], box, xywh=False)
                    # x1, y1, x2, y2 = box.numpy().tolist()
                    x1, y1, x2, y2 = xyxy
                    point_centre = (int(x1 + (x2-x1)/2), int(y1 + (y2-y1)/2))
                    if judge_in(detect_areass, point_centre):

                        #判断目标是否在区域内添加到detected_roi_list画框使用
                        
                        detect_box[track_id] = box
                        cv2.rectangle(frame_image, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 4 )
                        if iou > 0.97:
                            cv2.putText(frame_image, "stop,id=" + str(track_id), (int(x1) - 10, int(y1) - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 1, color[0], 2, )
                        else:
                            cv2.putText(frame_image, "move,id=" + str(track_id), (int(x1) - 10, int(y1) - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 1, color[1], 2, )
            track_history[track_id] = box
        

###########################################################################################################
    # if gd.pipe_dict[task_id] is not None:      
    draw_roi_box(detect_areass, frame_image)

    # if bool(detect_box): 
    # annotated_frame = detected_roi_list[0].plot()
    # frame_image = draw_bbox_box(frame_image, detected_roi_list,labels_list)

    cv2.imwrite('img/' + str(frame_count)+ '.jpg',frame_image)



    # try:
    #     gd.pipe_dict[task_id].stdin.write(frame_image.tobytes())
    # except Exception as e:
    #     logger.error(f'rtmp error: {e}')

    ###########################log打印
    # t5 = time.time()
    # cost = t5 - gd.lastt_dict[task_id]
    # gd.lastt_dict[task_id] = t5

    # logger.info(f'task id:{task_id}, fps {1.0/cost:.2f} ------')

    
