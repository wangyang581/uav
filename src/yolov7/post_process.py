import time
import cv2
from src.utils import convert_image_2_base64_str, draw_roi_box,draw_roi_person,judge_in,plot_bboxes
from .yolov7 import yolov7_detect
from .render import render_box, render_filled_box, get_text_size, render_text, RAND_COLORS
from .labels import COCOLabels
from .get_rule_info import get_rule_info
import numpy as np
from src.global_dict import gd 
import torch

def post_process(frame_image, 
                 logger, 
                 task_id,  
                 rule_info,
                 deepsort,
                 triton_client,
                 ):
    t0 = time.time()


    #调用triton对人进行检测
    t31 = time.time()
    detected_objects_person = yolov7_detect(frame_image,triton_client,[640,640],'dali_person_detect')
    t32 = time.time()
    print('person_dect',t32-t31)

    #获取rule_info里的信息
    box_detect_roi, person_detect_roi, time_detect_roi, event_check_duration = get_rule_info(rule_info,frame_image,logger,task_id)
   
 
    # 画出box_roi_rectangle区域
    draw_roi_box(box_detect_roi, frame_image)
    # 画出person_roi_rectangle区域
    draw_roi_person(person_detect_roi, frame_image)

    detected_result_list = [] #存放区域内检测结果
    class_list = [] #存放人
    for i in range(0,len(detected_objects_person)):
        
        box_p = detected_objects_person[i]
        box_p.classID = 7
        x1, y1, x2, y2 = box_p.box()
        point_centre = (int(x1 + (x2-x1)/2), int(y1 + (y2-y1)/2))

        if judge_in(person_detect_roi, point_centre):
            detected_result_list.append(box_p)

    if detected_result_list == []:
        if gd.pipe_dict[task_id] is not None:
        #返回结果视频流
            try:
                gd.pipe_dict[task_id].stdin.write(frame_image.tobytes())
            except Exception as e:
                logger.error(f'rtmp error: {e}')
    

####################################################对ROI内person进行跟踪########################################
    
    bbox_xywh = []
    bbox_xyxys = []
    confs = []
    clss = []
    for i in range(0,len(detected_result_list)):
        box_p_obj = detected_result_list[i]
        x1, y1, x2, y2 = box_p_obj.box()
        obj = [
            int((x1+x2)/2), int((y1+y2)/2),
            x2-x1, y2-y1
        ]

        obj_sort = [x1, y1, x2, y2, box_p_obj.confidence]

        bbox_xywh.append(obj)
        confs.append(box_p_obj.confidence)
        clss.append(box_p_obj.classID)

        bbox_xyxys.append(obj_sort)
    
#############deepsort#######################################
    t41 = time.time()
    xywhs = torch.Tensor(bbox_xywh)
    confss = torch.Tensor(confs)
    outputs = deepsort.update(xywhs, confss, clss, frame_image)
    bboxes2draw = []
    for value in list(outputs):
        # print(value)
        x1, y1, x2, y2, cls_, track_id = value
        bboxes2draw.append(
            (x1, y1, x2, y2, cls_, track_id)
        )
    frame_image = plot_bboxes(frame_image, bboxes2draw)
    t42 = time.time()
    print('sort',t42-t41)

#############sort############################
    # t1 = time.time()
    # bbox_xyxys=np.array(bbox_xyxys)
    # track_outputs = sort.update(bbox_xyxys)
    # t2 = time.time()
    # print(t2-t1)
    # for value in list(track_outputs):
    #     box = [int(b) for b in value[:4]]


####################################################################################################
    detected_result_list = []
    #调用triton对包裹进行检测
    t21 = time.time()
    detected_objects_box = yolov7_detect(frame_image,triton_client,[768,768],'dali_haining_box_detect')
    t22 = time.time()
    print('box_dect',t22-t21)

    for i in range(0,len(detected_objects_box)):
        box_b = detected_objects_box[i]
        
        x1, y1, x2, y2 = box_b.box()

        point_centre = (int(x1 + (x2-x1)/2), int(y1 + (y2-y1)/2))
        if judge_in(box_detect_roi, point_centre):
            detected_result_list.append(box_b)

    if gd.pipe_dict[task_id] is not None:
        ##画框
        for i in range(0,len(detected_result_list)):
            box = detected_result_list[i]
            frame_image = render_box(frame_image, box.box(), color=tuple(RAND_COLORS[box.classID % 64].tolist()))
            frame_image = render_text(frame_image, f"{COCOLabels(box.classID).name}: {box.confidence:.2f}", (box.x1, box.y1), color=(30, 30, 30), normalised_scaling=0.5)
            
            #print(box.classID)

        #返回结果视频流
        t11 = time.time()
        try:
            gd.pipe_dict[task_id].stdin.write(frame_image.tobytes())
        except Exception as e:
            logger.error(f'rtmp error: {e}')
        t12 = time.time()


    t4 = time.time()
    
    cost = t4 - gd.lastt_dict[task_id]
    gd.lastt_dict[task_id] = t4
    
    print(1.0/cost,cost)
    
    # logger.info(f'task id: {task_id}, dali_person_detect {(t32-t31)*1000:.1f}ms, dali_haining_box_detect {(t22-t21)*1000:.1f}ms, \
    #             push_result_image {(t12-t11)*1000:.1f}ms, deepsort_time {(t42-t41)*1000:.1f}ms,\
    #             fps {1.0/cost:.2f} ------'
    #             )


