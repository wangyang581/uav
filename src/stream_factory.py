import subprocess as sp

class StreamFactory():

    def __init__(self) -> None:
        pass

    def new_pipe(device_frame_rate, rtmp_server):
        command = [
            'ffmpeg',
            '-f', 'rawvideo', # 强制输入或输出文件格式
            '-vcodec','rawvideo', # 设置视频编解码器。这是-codec:v的别名
            '-pix_fmt', 'bgr24', # 设置像素格式
            #'-loglevel', 'quiet',
            '-s', "1920x1080", # 设置图像大小
            '-r', str(25), # 设置帧率
            '-i', '-', # 输入
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-preset', 'ultrafast',
            '-f', 'flv',# 强制输入或输出文件格式
            rtmp_server]

        return sp.Popen(command, stdin=sp.PIPE) 
         