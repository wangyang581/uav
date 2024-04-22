import sys
import os
import math
import torch
import logging, logging.handlers

import base64
from PIL import Image, ImageFont, ImageDraw
from io import BytesIO

import numpy as np
import cv2
import time

file_path = os.path.abspath(__file__)
file_path_arr = os.path.split(file_path)
font_path = os.path.join(file_path_arr[0], "simsun.ttc")


def generate_fixed_colors(num_colors):
    # 定义一些基本颜色
    base_colors = [
        (255, 0, 0),  # 红色
        (0, 255, 0),  # 绿色
        (0, 0, 255),  # 蓝色
        (255, 255, 0),  # 黄色
        (255, 0, 255),  # 粉红色
        (0, 255, 255),  # 青色
        (128, 0, 0),  # 深红色
        (0, 128, 0),  # 深绿色
        (0, 0, 128),  # 深蓝色
        (128, 128, 0),  # 橄榄色
        (128, 0, 128),  # 紫色
        (0, 128, 128),  # 灰绿色
    ]

    num_base_colors = len(base_colors)
    num_shades = num_colors // num_base_colors

    # 生成不同亮度的颜色
    colors = []
    for base_color in base_colors:
        for i in range(num_shades):
            brightness = int(255 * (i + 1) / num_shades)
            colors.append((base_color[0], base_color[1], base_color[2]))

    return colors


def person_in_list(pid, per_list):
    for i in range(0, len(per_list)):
        if pid in per_list[i]:
            return True
    return False


def id_in_list(ids, lists):
    for i in range(0, len(ids)):
        a = 0
        for j in range(0, len(lists)):
            if ids[i] in lists[j]:
                a += 1
        if a >= len(lists):
            return True

    return False


def id_in_list_2(ids, lists):
    for i in range(0, len(ids)):
        a = 0
        for j in range(0, len(lists)):
            if ids[i] in lists[j]:
                a += 1
        if a >= 13:
            return True

    return False


def id_in_list_3(ids, lists):
    for i in range(0, len(ids)):
        a = 0
        for j in range(0, len(lists)):
            if ids[i] in lists[j]:
                a += 1
        if a >= 1:
            return True

    return False


def draw_bbox_box(frame_image, detected_roi_list, labels_list):
    num_colors = 12
    fixed_colors = generate_fixed_colors(num_colors)

    # color = (255,0,0)
    for box in detected_roi_list:
        xyxy, cls, conf = box

        x1, y1, x2, y2 = xyxy

        cv2.rectangle(
            frame_image,
            (int(x1), int(y1)),
            (int(x2), int(y2)),
            fixed_colors[int(cls)],
            2,
        )

        frame_image = cv2.putText(
            frame_image,
            labels_list[int(cls)] + ",C=" + str(round(conf, 2)),
            (int(x1) - 10, int(y1) - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            fixed_colors[int(cls)],
            2,
        )

    return frame_image


def judge_line(point_line, point):
    # 判断点往右延伸是否与线段相交，相交返回true，不想交返回false
    x = point[0]
    y = point[1]
    x1 = point_line[0][0]
    y1 = point_line[0][1]
    x2 = point_line[1][0]
    y2 = point_line[1][1]
    if y1 > y2:  # 确认在上方的点，用该点做减数来计算斜率
        ymax = y1
        xmax = x1
        ymin = y2
        xmin = x2
    else:
        ymax = y2
        ymin = y1
        xmax = x2
        xmin = x1
    if y >= ymax or y <= ymin:  # 点不在线段的垂直范围里不可能相交
        return False
    if x >= max(x1, x2):  # 点在线段的右侧也不可能相交
        return False
    k_line = 0
    k_point = 0
    if x1 == x2:  # 针对横坐标或纵坐标相等做的一些处理
        k_line = 100
    if y1 == y2:
        k_line = 0.01
    if k_line == 0:
        k_line = (ymax - ymin) / (xmax - xmin)
    if x == xmax:
        k_point = 100
    if y == ymax:
        k_point = 0.01
    if k_point == 0:
        k_point = (ymax - y) / (xmax - x)
    if k_line > 0:  # 线段斜率可能是正负，点可能在线段的左右侧，分类讨论
        if k_point < k_line:
            return True
        else:
            return False
    else:
        if k_point > 0:
            return True
        else:
            if k_line > k_point:
                return True
    return False


[394, 187], [565, 171], [587, 530], [379, 534]


def is_intersect(rect, polygon):
    """
    判断矩形和多边形是否相交。

    Parameters:
        rect (tuple): 矩形的坐标 (left, top, right, bottom)。
        polygon (list): 多边形的顶点坐标 [(x1, y1), (x2, y2), ...]。

    Returns:
        bool: 如果矩形与多边形相交返回 True，否则返回 False。
    """
    rect_left, rect_top, rect_right, rect_bottom = rect

    # 检查矩形的边界是否与多边形的边界相交
    for i in range(len(polygon)):
        # 获取多边形的当前边
        p1 = polygon[i]
        p2 = polygon[(i + 1) % len(polygon)]
        poly_left, poly_top = min(p1[0], p2[0]), min(p1[1], p2[1])
        poly_right, poly_bottom = max(p1[0], p2[0]), max(p1[1], p2[1])

        # 判断矩形和多边形边界是否相交
        if (
            rect_right >= poly_left
            and rect_left <= poly_right
            and rect_bottom >= poly_top
            and rect_top <= poly_bottom
        ):
            return True

    return False


def is_inside(inner_rect, outer_rect):
    """
    检查内部矩形是否完全位于外部矩形内部。

    Parameters:
        inner_rect (tuple): 内部矩形的坐标 (left, top, right, bottom)。
        outer_rect (tuple): 外部矩形的坐标 (left, top, right, bottom)。

    Returns:
        bool: 如果内部矩形完全位于外部矩形内部返回 True，否则返回 False。
    """
    # 提取内部和外部矩形的坐标
    inner_left, inner_top, inner_right, inner_bottom = inner_rect
    outer_left, outer_top, outer_right, outer_bottom = outer_rect

    # 检查内部矩形的四个顶点是否都在外部矩形内部
    if (
        inner_left >= outer_left
        and inner_right <= outer_right
        and inner_top >= outer_top
        and inner_bottom <= outer_bottom
    ):
        return True
    else:
        return False


def judge_in(point_list, point):
    # 该点向右的射线与多边形的交点数为奇数则在多边形内，偶数则在外
    # 遍历线段，比较y值，point的y处于线段y值中间则相交
    # 多边形坐标按下笔顺序，因为顺序不同，多边形围合的形状也不同，比如五个点，可以使五角星，也可是五边形
    # 在多边形内返回true，不在返回false
    num_intersect = 0  # 交点数
    num_intersect_vertex = (
        0  # 点与顶点的纵坐标相同的数量，用一下方法纵坐标相同时会计算两次交点数（一个点是两个线段的顶点），最后减去（相当于只计算一次）
    )
    for item in point_list:
        if item[1] == point[1]:
            num_intersect_vertex += 1
    x = point[0]
    y = point[1]
    for i in range(len(point_list) - 1):
        point_line = [point_list[i], point_list[i + 1]]
        if judge_line(point_line, point):
            num_intersect += 1
    xb = point_list[0][0]  # 首尾坐标的线段
    yb = point_list[0][1]
    xe = point_list[-1][0]
    ye = point_list[-1][1]
    point_lines = [(xb, yb), (xe, ye)]
    if judge_line(point_lines, point):
        num_intersect += 1
    # print("与多变形交点的个数为：%d"%num_intersect)
    num_intersect -= num_intersect_vertex
    if num_intersect > 0 and num_intersect % 2 == 1:
        return True
    else:
        return False


def draw_roi_box(point_list, img):
    # 将点依次连接，并将需要判断的点画出来
    for i in range(len(point_list) - 1):
        x1 = point_list[i][0]
        y1 = point_list[i][1]
        x2 = point_list[i + 1][0]
        y2 = point_list[i + 1][1]
        cv2.line(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
    xb = point_list[0][0]
    yb = point_list[0][1]
    xe = point_list[-1][0]
    ye = point_list[-1][1]
    cv2.line(img, (xb, yb), (xe, ye), (0, 255, 0), 2)


def get_logger(log_dir, log_file="log.txt"):
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    filename = os.path.join(log_dir, log_file)
    log_format = "%(asctime)s %(message)s"

    logger = logging.getLogger(log_file.split(".")[0])
    logger.setLevel(level=logging.INFO)

    # file_handler = logging.FileHandler(filename)
    file_handler = logging.handlers.RotatingFileHandler(
        filename, maxBytes=100 * 1024 * 1024, backupCount=9
    )
    file_handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(stream_handler)

    return logger


def convert_image_2_base64_str(image, format="JPEG"):
    img = Image.fromarray(image[:, :, ::-1])
    output_buffer = BytesIO()
    img = img.convert("RGB")
    img.save(output_buffer, format=format)
    byte_data = output_buffer.getvalue()
    return base64.b64encode(byte_data).decode("utf-8")


def drawImg(img_opencv, box_arr, text_arr, color_arr, text_size=20):
    for box, color in zip(box_arr, color_arr):
        cv2.rectangle(img_opencv, box[0:2], box[2:4], color, 2)

    img_pil = Image.fromarray(img_opencv)
    font = ImageFont.truetype(font_path, text_size)

    draw = ImageDraw.Draw(img_pil)
    for box, text, color in zip(box_arr, text_arr, color_arr):
        if not isinstance(text, np.unicode):
            text = text.decode("utf8")
        draw.text((box[0], box[1] - text_size), text, font=font, fill=color)
    return np.asarray(img_pil)


class HeartBeat:
    def __init__(self, id, threshold=3 * 60):
        self.id = id
        self.threshold = threshold
        self.last_beat = int(time.time())

    def is_alive(self):
        now = int(time.time())
        return now - self.last_beat < self.threshold

    def beat(self):
        self.last_beat = int(time.time())


class AverageMeter:
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


def bbox_iou(box1, box2, xywh=True, GIoU=False, DIoU=False, CIoU=False, eps=1e-7):
    """
    Calculate Intersection over Union (IoU) of box1(1, 4) to box2(n, 4).

    Args:
        box1 (torch.Tensor): A tensor representing a single bounding box with shape (1, 4).
        box2 (torch.Tensor): A tensor representing n bounding boxes with shape (n, 4).
        xywh (bool, optional): If True, input boxes are in (x, y, w, h) format. If False, input boxes are in
                               (x1, y1, x2, y2) format. Defaults to True.
        GIoU (bool, optional): If True, calculate Generalized IoU. Defaults to False.
        DIoU (bool, optional): If True, calculate Distance IoU. Defaults to False.
        CIoU (bool, optional): If True, calculate Complete IoU. Defaults to False.
        eps (float, optional): A small value to avoid division by zero. Defaults to 1e-7.

    Returns:
        (torch.Tensor): IoU, GIoU, DIoU, or CIoU values depending on the specified flags.
    """

    # Get the coordinates of bounding boxes
    if xywh:  # transform from xywh to xyxy
        (x1, y1, w1, h1), (x2, y2, w2, h2) = box1.chunk(4, -1), box2.chunk(4, -1)
        w1_, h1_, w2_, h2_ = w1 / 2, h1 / 2, w2 / 2, h2 / 2
        b1_x1, b1_x2, b1_y1, b1_y2 = x1 - w1_, x1 + w1_, y1 - h1_, y1 + h1_
        b2_x1, b2_x2, b2_y1, b2_y2 = x2 - w2_, x2 + w2_, y2 - h2_, y2 + h2_
    else:  # x1, y1, x2, y2 = box1
        b1_x1, b1_y1, b1_x2, b1_y2 = box1.chunk(4, -1)
        b2_x1, b2_y1, b2_x2, b2_y2 = box2.chunk(4, -1)
        w1, h1 = b1_x2 - b1_x1, b1_y2 - b1_y1 + eps
        w2, h2 = b2_x2 - b2_x1, b2_y2 - b2_y1 + eps

    # Intersection area
    inter = (b1_x2.minimum(b2_x2) - b1_x1.maximum(b2_x1)).clamp_(0) * (
        b1_y2.minimum(b2_y2) - b1_y1.maximum(b2_y1)
    ).clamp_(0)

    # Union Area
    union = w1 * h1 + w2 * h2 - inter + eps

    # IoU
    iou = inter / union
    if CIoU or DIoU or GIoU:
        cw = b1_x2.maximum(b2_x2) - b1_x1.minimum(
            b2_x1
        )  # convex (smallest enclosing box) width
        ch = b1_y2.maximum(b2_y2) - b1_y1.minimum(b2_y1)  # convex height
        if CIoU or DIoU:  # Distance or Complete IoU https://arxiv.org/abs/1911.08287v1
            c2 = cw**2 + ch**2 + eps  # convex diagonal squared
            rho2 = (
                (b2_x1 + b2_x2 - b1_x1 - b1_x2) ** 2
                + (b2_y1 + b2_y2 - b1_y1 - b1_y2) ** 2
            ) / 4  # center dist ** 2
            if (
                CIoU
            ):  # https://github.com/Zzh-tju/DIoU-SSD-pytorch/blob/master/utils/box/box_utils.py#L47
                v = (4 / math.pi**2) * (
                    torch.atan(w2 / h2) - torch.atan(w1 / h1)
                ).pow(2)
                with torch.no_grad():
                    alpha = v / (v - iou + (1 + eps))
                return iou - (rho2 / c2 + v * alpha)  # CIoU
            return iou - rho2 / c2  # DIoU
        c_area = cw * ch + eps  # convex area
        return (
            iou - (c_area - union) / c_area
        )  # GIoU https://arxiv.org/pdf/1902.09630.pdf
    return iou  # IoU
