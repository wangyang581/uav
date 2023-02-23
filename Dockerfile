FROM nvcr.io/nvidia/tritonserver:22.04-py3

RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys A4B469963BF863CC

RUN sed -i 's#http://archive.ubuntu.com/#http://mirrors.tuna.tsinghua.edu.cn/#' /etc/apt/sources.list
RUN apt update 
#RUN apt upgrade -y

apt-get install -y libgl1-mesa-glx ffmpeg git python3 python-dev python3.8-dev cmake g++ \
    build-essential libglib2.0-dev libglib2.0-dev-bin python-gi-dev libtool m4 autoconf automake \
    lsb-release redis

ENV DEBIAN_FRONTEND=noninteractive
RUN apt install -y git build-essential yasm cmake libtool libc6 libc6-dev unzip wget libnuma1 libnuma-dev \
libgl1-mesa-glx libglib2.0-dev libglib2.0-dev-bin m4 autoconf automake

WORKDIR /workspace
#RUN git clone -b n11.1.5.2 https://github.com/FFmpeg/nv-codec-headers.git
#RUN git clone -b n4.4.3 https://github.com/FFmpeg/FFmpeg.git
#RUN git clone -b 4.5.5 https://github.com/opencv/opencv.git
#RUN git clone -b 4.5.5 https://github.com/opencv/opencv_contrib.git
COPY nv-codec-headers-n11.1.5.2.zip /workspace
RUN unzip nv-codec-headers-n11.1.5.2.zip
COPY FFmpeg-n4.4.3.zip /workspace
RUN unzip FFmpeg-n4.4.3.zip 
COPY opencv-4.5.5.zip /workspace
RUN unzip opencv-4.5.5.zip
COPY opencv_contrib-4.5.5.zip /workspace 
RUN unzip opencv_contrib-4.5.5.zip

COPY Video_Codec_SDK_11.1.5.zip /workspace
RUN unzip Video_Codec_SDK_11.1.5.zip

WORKDIR /workspace/nv-codec-headers-n11.1.5.2
RUN make install 

WORKDIR /workspace/FFmpeg-n4.4.3
RUN ./configure --enable-nonfree --enable-cuda-nvcc --nvccflags="-gencode arch=compute_86,code=sm_86 -O2" \
--enable-libnpp --extra-cflags=-I/usr/local/cuda/include --extra-ldflags=-L/usr/local/cuda/lib64 \
--disable-static --enable-shared
RUN make -j8
RUN make install 

WORKDIR /workspace
RUN cp Video_Codec_SDK_11.1.5/Interface/* /usr/local/cuda/include 
RUN cp Video_Codec_SDK_11.1.5/Lib/linux/stubs/x86_64/* /usr/local/cuda/lib64/stubs 
RUN cp Video_Codec_SDK_11.1.5/Interface/* /usr/include 
RUN cp Video_Codec_SDK_11.1.5/Lib/linux/stubs/x86_64/* /usr/lib/x86_64-linux-gnu 

RUN apt install -y python3-dev python3-pip python3-numpy gcc g++ \
libpng-dev libjpeg-dev libopenexr-dev libtiff-dev libwebp-dev libgtk2.0-dev libgtkglext1-dev

RUN mkdir /workspace/opencv-4.5.5/build
WORKDIR /workspace/opencv-4.5.5/build

RUN cmake .. \
-D CMAKE_BUILD_TYPE=RELEASE \
-D CMAKE_INSTALL_PREFIX=/usr/local \
-D ENABLE_FAST_MATH=1 \
-D WITH_CUDA=ON \
-D WITH_CUDNN=ON \
-D CUDA_ARCH_BIN=8.6 \
-D CUDA_FAST_MATH=1 \
-D WITH_CUBLAS=1 \
-D WITH_FFMPEG=ON \
-D WITH_NVCUVID=ON \
-D WITH_OPENGL=ON \
-D WITH_V4L=ON \
-D WITH_LIBV4L=ON \
-D WITH_GTK_2_X=ON \
-D WITH_TBB=ON \
-D OPENCV_PYTHON3_VERSION=3.8 \
-D PYTHON3_EXECUTABLE=/usr/bin/python3.8 \
-D PYTHON3_INCLUDE_DIR=/usr/include/python3.8 \
-D PYTHON3_LIBRARY=/usr/lib/x86_64-linux-gnu/libpython3.8.so \
-D BUILD_opencv_python3=ON \
-D HAVE_opencv_python3=ON \
-D CUDNN_INCLUDE_DIR=/usr/include \
-D CUDNN_LIBRARY=/usr/lib/x86_64-linux-gnu/libcudnn.so.8.4.0 \
-D OPENCV_EXTRA_MODULES_PATH=/workspace/opencv_contrib-4.5.5/modules \
-D CMAKE_LIBRARY_PATH=/usr/local/cuda/lib64/stubs 

RUN make -j8
RUN make install 

WORKDIR /workspace/opencv-4.5.5/build/python_loader
RUN python3 setup.py install --install-lib=/usr/local/lib/python3.8/dist-packages

RUN pip3 install flask \
    scikit-image \
    scikit-learn \
    numba \
    filterpy \
    gevent \
    redis \
    tritonclient[all] \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

RUN cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime

WORKDIR /workspace
