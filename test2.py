import cv2

# 视频文件名
video_file = '/media/fengjin/新加卷/mydate/post_office/测试视频/xiashi.mp4'

# 打开视频文件
cap = cv2.VideoCapture(video_file)

# 逐帧读取视频文件
while True:
    ret, frame = cap.read()
    if not ret:
        break

    # 在这里对图像帧进行处理，如显示、保存等
    cv2.imwrite('1.jpg', frame)
    
    # 按下 'q' 键退出循环
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 释放资源
cap.release()
cv2.destroyAllWindows()
