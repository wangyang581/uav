import threading
from ultralytics import YOLO
# 加载目标检测模型的函数

# 创建一个全局的锁，用于保证模型加载的互斥访问
model_lock = threading.Lock()

def load_model():
    # 在这里加载目标检测模型
    # 这里只是一个示例，你需要根据你的实际情况来加载模型
    model_v8 = YOLO('src/ultralytics/weight/person/best.engine')
    box_model_v8 = YOLO('src/ultralytics/weight/hnyz/all_img/best.engine')
    return model_v8

# 子线程执行的函数
def inference_worker(image, model):
    # 在这里执行图像推理
    # 这里只是一个示例，你需要根据你的实际情况来执行推理
    model_lock.acquire()

    result = model.predict(source=image, imgsz=640, device=0, iou=0.7, conf=0.25)

    model_lock.release()
    print(result)

# 主线程加载模型

model = load_model()

# 创建多个子线程进行图像推理
num_threads = 1  # 设置子线程数量
image = 'mask.mp4'  # 要进行推理的图像数据
threads = []

i=1
for _ in range(num_threads):
    i+=1
    print(i)
    t = threading.Thread(target=inference_worker, args=(image, model))
    threads.append(t)
    print(len(threads))
    t.start()

# # 等待所有子线程完成
# for t in threads:
#     t.join()
