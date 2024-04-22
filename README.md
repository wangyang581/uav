# Face Server Opencv Gpu Inference Engine

## 1，Dependencies

### 1.1 Triton
* [Triton](https://developer.nvidia.com/nvidia-triton-inference-server) 是 NVIDIA 推出的 Inference Server，提供 AI 模型的部署服务。客户端可以使用 HTTP/REST 或 gRPC 的方式来请求服务。支持各种深度学习后端，支持 k8s，和多种批处理算法。
* 下载triton的镜像 nvcr.io/nvidia/tritonserver:22.04-py3

### 1.2 Opencv
* 使用Dockfile编译拥有gpu视频解码功能的opencv

### 1.3 gRPC
* 参考 https://grpc.io/docs/languages/python/quickstart/
* `cd src/grpc_py`
* `python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. inference_result.proto`
* 将 `inference_result_pb2_grpc.py` 第五行改为 `from . import inference_result_pb2 as inference__result__pb2`

### 1.4 redis
* 用来储存人脸特征

## 2，Quickstart

### 2.1 启动服务
> 启动命令：bash start_server.sh

#### 2.1.1 redis参数
```
port:   调用redis数据库的端口，默认6379
```

#### 2.1.2 tritonserver参数
```
http-port:                      http请求的端口，默认8000
grpc-port:                      grpc请求的端口，默认8001
metrics-port:                   metrics请求的端口，默认8002
model-repository:               需要部署的模型文件夹位置
strict-model-config:            模型配置文件时候严格，需要输入False
```

#### 2.1.3 flask server参数
```
triton_port:                    必须和tritionserver参数里的http-port保持一致，默认8000
redis_port:                     必须和redis参数里的port保持一致，默认6379
rtmp_server_uri:                推流服务器地址，默认为rtmp://10.0.109.88:1935/live/frtask
```

### 2.2 接口说明

#### 2.2.1 添加视频流推理任务

* 发送post请求，默认地址http://127.0.0.1:5000/add_source
* 参数如下
```
task_id: str,                   任务id（必填）
rtsp_url: str,                  需要推理的流（必填）
grpc_address: str,              回调地址
frame_rate: int,                视频推送频率，默认25
rule_info: str,                 算法解析规则(json)
```
* rule_info内容说明（除mode之外，其他参数都能通过update_source接口来动态更新）
```
mode: str,                      opencv解码模式，cpu或者gpu
skip_frame_rate: int            跳帧策略，小于等于0时取实时帧处理，等于1时每帧都处理，大于1时每n帧处理一帧
add_stranger: int               0表示不把该摄像头下拍摄到的陌生人加入陌生人数据库，1表示加入数据库
alert_time: int                 n秒之内警报过的陌生人不再重复发送警报，默认60
```
* 命令如下：
```
curl -X POST \
-F task_id=2 \
-F rtsp_url=rtsp://admin:zjlab2022@10.0.106.112:554/Streaming/Channels/101 \
-F grpc_address=10.0.106.188:50051 \
-F frame_rate=25 \
-F rule_info='{"mode":"gpu", "skip_frame_rate": 1, "add_stranger":1, "alert_time": 60}' \
http://10.0.106.188:5000/add_source
```
* 返回正在运行的推理任务task_id列表

#### 2.2.2 删除视频流推理任务

* 发送delete请求，默认地址http://127.0.0.1:5000/remove_source
* 参数如下
```
task_id: str,                   任务id
```
* 命令如下
```
curl -X DELETE \
-F task_id=2 \
http://10.0.106.188:5000/remove_source
```
* 返回正在运行的推理任务task_id列表

#### 2.2.3 重建视频流推理任务

* 发送post请求，默认地址http://127.0.0.1:5000/rebuild_source
* 参数如下
```
task_id: str,                   任务id
rtsp_url: str,                  需要推理的流
grpc_address: str,              回调地址
frame_rate: int,                视频推送频率，默认25
rule_info: str,                 算法解析规则(json)
```
* 命令如下
```
curl -X POST \
-F task_id=2 \
-F rtsp_url=rtsp://admin:zjlab2022@10.0.106.112:554/Streaming/Channels/101 \
-F grpc_address=10.0.106.188:50051 \
-F frame_rate=25 \
-F rule_info='' \
http://10.0.106.188:5000/rebuild_source
```
* 返回参数
```
source_list:                    正在运行的推理任务task_id列表
```

#### 2.2.4 获取所有视频流推理任务

* 发送post请求，默认地址http://127.0.0.1:5000/get_source_list
* 无参数，命令如下
```
curl -X POST \
http://10.0.106.188:5000/get_source_list
```
* 返回正在运行的推理任务task_id列表

#### 2.2.5 查询视频流推理任务的状态

* 发送post请求，默认地址http://127.0.0.1:5000/source_status
* 已json格式输入task_id的数组，命令如下
```
curl -X POST \
-d '["1", "2", "3"]' \
-H "Content-type: application/json" \
http://10.0.106.188:5000/source_status
```
* 返回各个推理任务task_id的运行状态

#### 2.2.6 更新视频流推理任务的参数

* 发送post请求，默认地址http://127.0.0.1:5000/update_source
* 参数如下
```
task_id: str,                   任务id
frame_rate: int,                视频推送频率，默认25
rule_info: str,                 算法解析规则(json)
```
* 命令如下
```
curl -X PUT \
-F task_id=2 \
-F rule_info='{"mode":"gpu", "skip_frame_rate": 2, "add_stranger":1, "alert_time": 300}' \
http://10.0.106.188:5000/update_source
```
* 返回正在运行的推理任务task_id列表

#### 2.2.7 创建推流任务

* 发送post请求，默认地址http://127.0.0.1:5000/stream/pipe
* 已json格式输入task_id的数组，命令如下
```
curl -X POST \
-d '["1", "2", "3"]' \
-H "Content-type: application/json" \
http://10.0.106.188:5000/stream/pipe
```
* 返回成功创建推流任务的task_id

#### 2.2.8 删除推流任务

* 发送delete请求，默认地址http://127.0.0.1:5000/stream/pipe
* 已json格式输入task_id的数组，命令如下
```
curl -X DELETE \
-d '["1", "2", "3"]' \
-H "Content-type: application/json" \
http://10.0.106.188:5000/stream/pipe
```
* 返回成功删除推流任务的task_id

#### 2.2.9 图片人脸识别

* 发送post请求，默认地址http://127.0.0.1:5000/image_recog
* 参数如下
```
img_url: str,                   图片的url地址
```
* 命令如下
```
curl -X POST \
-F img_url=http://p0.itc.cn/q_70/images03/20220927/d551fe874da04362aa9cb4a0bf748a12.jpeg \
http://10.0.106.188:5000/image_recog
```
* 返回识别到的人脸信息，人脸名称，置信度，人脸框

#### 2.2.10 添加人脸

* 发送post请求，默认地址http://127.0.0.1:5000/add_face
* 参数如下
```
face_name: str,                 人脸名称
img_url: str,                   人脸图片地址
```
* 命令如下
```
curl -X POST \
-F face_name=张三 \
-F img_url=http://p0.itc.cn/q_70/images03/20220927/d551fe874da04362aa9cb4a0bf748a12.jpeg \
http://10.0.106.188:5000/add_face
```
* 返回人脸库中已有的人脸face_name列表

#### 2.2.11 删除人脸

* 发送delete请求，默认地址http://127.0.0.1:5000/del_face
* 参数如下
```
face_name: str,                 人脸名称
```
* 命令如下
```
curl -X DELETE \
-F face_name=张三 \
http://10.0.106.188:5000/del_face
```
* 返回人脸库中已有的人脸face_name列表

#### 2.2.12 获取人脸列表

* 发送post请求，默认地址http://127.0.0.1:5000/get_face_list
* 无参数，命令如下
```
curl -X POST \
http://10.0.106.188:5000/get_face_list
```
* 返回人脸库中已有的人脸face_name列表


海宁侠石顺风：
box:[(376,175),(702,180),(714,534),(351,535)]
person:[(10,532),(62,0),(383,1),(353,527)]