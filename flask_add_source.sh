curl -X POST \
-F task_id=21 \
-F rtsp_url='rtsp://admin:admin123@10.255.1.50:554/cam/realmonitor?channel=1&subtype=0' \
-F rtmp_address=rtmp://10.0.109.88:1935/live/ \
-F rule_info='{}' \
http://10.255.198.101:5000/add_source