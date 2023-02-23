import subprocess as sp

class StreamFactory():

    def __init__(self) -> None:
        pass

    def new_pipe(device_frame_rate, rtmp_server):
        command = [
            'ffmpeg',
            '-y',
            '-f', 'rawvideo',
            '-pix_fmt', 'bgr24',
            '-s', '1920x1080',
            '-r', str(device_frame_rate),
            '-i', '-',
            '-pix_fmt', 'yuv420p',
            '-f', 'flv',
            rtmp_server]

        return sp.Popen(command, stdin=sp.PIPE) 
         