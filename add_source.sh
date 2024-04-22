curl -X POST \
-F task_id=1 \
-F rtsp_url='rtsp://admin:admin123@10.255.1.50:554/cam/realmonitor?channel=1&subtype=0' \
-F grpc_address=10.0.106.188:50051 \
-F rtmp_address=rtmp://10.0.109.88:1935/live/ \
-F rule_info='{"event_check_duration":10,"detect_areas1":"[(409,94),(600,98),(600,536),(338,517)]","person_areas1":"[(600,105),(965,164),(990,531),(613,539)]"}' \
http://10.255.198.101:5000/add_source

curl -X POST \
-F task_id=2 \
-F rtsp_url='rtsp://admin:admin123@10.255.1.51:554/cam/realmonitor?channel=1&subtype=0' \
-F grpc_address=10.0.106.188:50051 \
-F rtmp_address=rtmp://10.0.109.88:1935/live/ \
-F rule_info='{"event_check_duration":10,"detect_areas1":"[(409,94),(600,98),(600,536),(338,517)]","person_areas1":"[(600,105),(965,164),(990,531),(613,539)]"}' \
http://10.255.198.101:5000/add_source

curl -X POST \
-F task_id=3 \
-F rtsp_url='rtsp://admin:admin123@10.255.1.52:554/cam/realmonitor?channel=1&subtype=0' \
-F grpc_address=10.0.106.188:50051 \
-F rtmp_address=rtmp://10.0.109.88:1935/live/ \
-F rule_info='{"event_check_duration":10,"detect_areas1":"[(409,94),(600,98),(600,536),(338,517)]","person_areas1":"[(600,105),(965,164),(990,531),(613,539)]"}' \
http://10.255.198.101:5000/add_source

curl -X POST \
-F task_id=4 \
-F rtsp_url='rtsp://admin:admin@10.255.1.54:554/cam/realmonitor?channel=1&subtype=0' \
-F grpc_address=10.0.106.188:50051 \
-F rtmp_address=rtmp://10.0.109.88:1935/live/ \
-F rule_info='{"event_check_duration":10,"detect_areas1":"[(409,94),(600,98),(600,536),(338,517)]","person_areas1":"[(600,105),(965,164),(990,531),(613,539)]"}' \
http://10.255.198.101:5000/add_source

curl -X POST \
-F task_id=5 \
-F rtsp_url='rtsp://admin:admin@10.255.1.56:554/cam/realmonitor?channel=1&subtype=0' \
-F grpc_address=10.0.106.188:50051 \
-F rtmp_address=rtmp://10.0.109.88:1935/live/ \
-F rule_info='{"event_check_duration":10,"detect_areas1":"[(409,94),(600,98),(600,536),(338,517)]","person_areas1":"[(600,105),(965,164),(990,531),(613,539)]"}' \
http://10.255.198.101:5000/add_source

curl -X POST \
-F task_id=6 \
-F rtsp_url='rtsp://admin:admin@10.255.1.60:554/cam/realmonitor?channel=1&subtype=0' \
-F grpc_address=10.0.106.188:50051 \
-F rtmp_address=rtmp://10.0.109.88:1935/live/ \
-F rule_info='{"event_check_duration":10,"detect_areas1":"[(409,94),(600,98),(600,536),(338,517)]","person_areas1":"[(600,105),(965,164),(990,531),(613,539)]"}' \
http://10.255.198.101:5000/add_source

curl -X POST \
-F task_id=7 \
-F rtsp_url='rtsp://admin:admin@10.255.1.61:554/cam/realmonitor?channel=1&subtype=0' \
-F grpc_address=10.0.106.188:50051 \
-F rtmp_address=rtmp://10.0.109.88:1935/live/ \
-F rule_info='{"event_check_duration":10,"detect_areas1":"[(409,94),(600,98),(600,536),(338,517)]","person_areas1":"[(600,105),(965,164),(990,531),(613,539)]"}' \
http://10.255.198.101:5000/add_source

curl -X POST \
-F task_id=8 \
-F rtsp_url='rtsp://admin:admin@10.255.1.62:554/cam/realmonitor?channel=1&subtype=0' \
-F grpc_address=10.0.106.188:50051 \
-F rtmp_address=rtmp://10.0.109.88:1935/live/ \
-F rule_info='{"event_check_duration":10,"detect_areas1":"[(409,94),(600,98),(600,536),(338,517)]","person_areas1":"[(600,105),(965,164),(990,531),(613,539)]"}' \
http://10.255.198.101:5000/add_source

curl -X POST \
-F task_id=9 \
-F rtsp_url='rtsp://admin:admin123@10.255.1.64:554/cam/realmonitor?channel=1&subtype=0' \
-F grpc_address=10.0.106.188:50051 \
-F rtmp_address=rtmp://10.0.109.88:1935/live/ \
-F rule_info='{"event_check_duration":10,"detect_areas1":"[(409,94),(600,98),(600,536),(338,517)]","person_areas1":"[(600,105),(965,164),(990,531),(613,539)]"}' \
http://10.255.198.101:5000/add_source

curl -X POST \
-F task_id=10 \
-F rtsp_url='rtsp://admin:admin123@10.255.1.65:554/cam/realmonitor?channel=1&subtype=0' \
-F grpc_address=10.0.106.188:50051 \
-F rtmp_address=rtmp://10.0.109.88:1935/live/ \
-F rule_info='{"event_check_duration":10,"detect_areas1":"[(409,94),(600,98),(600,536),(338,517)]","person_areas1":"[(600,105),(965,164),(990,531),(613,539)]"}' \
http://10.255.198.101:5000/add_source

curl -X POST \
-F task_id=11 \
-F rtsp_url='rtsp://admin:admin123@10.255.1.67:554/cam/realmonitor?channel=1&subtype=0' \
-F grpc_address=10.0.106.188:50051 \
-F rtmp_address=rtmp://10.0.109.88:1935/live/ \
-F rule_info='{"event_check_duration":10,"detect_areas1":"[(409,94),(600,98),(600,536),(338,517)]","person_areas1":"[(600,105),(965,164),(990,531),(613,539)]"}' \
http://10.255.198.101:5000/add_source

curl -X POST \
-F task_id=12 \
-F rtsp_url='rtsp://admin:admin123@10.255.1.68:554/cam/realmonitor?channel=1&subtype=0' \
-F grpc_address=10.0.106.188:50051 \
-F rtmp_address=rtmp://10.0.109.88:1935/live/ \
-F rule_info='{"event_check_duration":10,"detect_areas1":"[(409,94),(600,98),(600,536),(338,517)]","person_areas1":"[(600,105),(965,164),(990,531),(613,539)]"}' \
http://10.255.198.101:5000/add_source

curl -X POST \
-F task_id=13 \
-F rtsp_url='rtsp://admin:admin@10.255.1.70:554/cam/realmonitor?channel=1&subtype=0' \
-F grpc_address=10.0.106.188:50051 \
-F rtmp_address=rtmp://10.0.109.88:1935/live/ \
-F rule_info='{"event_check_duration":10,"detect_areas1":"[(409,94),(600,98),(600,536),(338,517)]","person_areas1":"[(600,105),(965,164),(990,531),(613,539)]"}' \
http://10.255.198.101:5000/add_source

curl -X POST \
-F task_id=14 \
-F rtsp_url='rtsp://admin:admin123@10.255.1.71:554/cam/realmonitor?channel=1&subtype=0' \
-F grpc_address=10.0.106.188:50051 \
-F rtmp_address=rtmp://10.0.109.88:1935/live/ \
-F rule_info='{"event_check_duration":10,"detect_areas1":"[(409,94),(600,98),(600,536),(338,517)]","person_areas1":"[(600,105),(965,164),(990,531),(613,539)]"}' \
http://10.255.198.101:5000/add_source

curl -X POST \
-F task_id=15 \
-F rtsp_url='rtsp://admin:admin@10.255.1.72:554/cam/realmonitor?channel=1&subtype=0' \
-F grpc_address=10.0.106.188:50051 \
-F rtmp_address=rtmp://10.0.109.88:1935/live/ \
-F rule_info='{"event_check_duration":10,"detect_areas1":"[(409,94),(600,98),(600,536),(338,517)]","person_areas1":"[(600,105),(965,164),(990,531),(613,539)]"}' \
http://10.255.198.101:5000/add_source

curl -X POST \
-F task_id=16 \
-F rtsp_url='rtsp://admin:admin123@10.255.1.73:554/cam/realmonitor?channel=1&subtype=0' \
-F grpc_address=10.0.106.188:50051 \
-F rtmp_address=rtmp://10.0.109.88:1935/live/ \
-F rule_info='{"event_check_duration":10,"detect_areas1":"[(409,94),(600,98),(600,536),(338,517)]","person_areas1":"[(600,105),(965,164),(990,531),(613,539)]"}' \
http://10.255.198.101:5000/add_source

curl -X POST \
-F task_id=17 \
-F rtsp_url='rtsp://admin:admin@10.255.1.74:554/cam/realmonitor?channel=1&subtype=0' \
-F grpc_address=10.0.106.188:50051 \
-F rtmp_address=rtmp://10.0.109.88:1935/live/ \
-F rule_info='{"event_check_duration":10,"detect_areas1":"[(409,94),(600,98),(600,536),(338,517)]","person_areas1":"[(600,105),(965,164),(990,531),(613,539)]"}' \
http://10.255.198.101:5000/add_source

curl -X POST \
-F task_id=18 \
-F rtsp_url='rtsp://admin:admin123@10.255.1.75:554/cam/realmonitor?channel=1&subtype=0' \
-F grpc_address=10.0.106.188:50051 \
-F rtmp_address=rtmp://10.0.109.88:1935/live/ \
-F rule_info='{"event_check_duration":10,"detect_areas1":"[(409,94),(600,98),(600,536),(338,517)]","person_areas1":"[(600,105),(965,164),(990,531),(613,539)]"}' \
http://10.255.198.101:5000/add_source

curl -X POST \
-F task_id=19 \
-F rtsp_url='rtsp://admin:admin@10.255.1.76:554/cam/realmonitor?channel=1&subtype=0' \
-F grpc_address=10.0.106.188:50051 \
-F rtmp_address=rtmp://10.0.109.88:1935/live/ \
-F rule_info='{"event_check_duration":10,"detect_areas1":"[(409,94),(600,98),(600,536),(338,517)]","person_areas1":"[(600,105),(965,164),(990,531),(613,539)]"}' \
http://10.255.198.101:5000/add_source

curl -X POST \
-F task_id=20 \
-F rtsp_url='rtsp://admin:zjlab2022@10.0.106.112:554/Streaming/Channels/101' \
-F grpc_address=10.0.106.188:50051 \
-F rtmp_address=rtmp://10.0.109.88:1935/live/ \
-F rule_info='{"event_check_duration":10,"detect_areas1":"[(409,94),(600,98),(600,536),(338,517)]","person_areas1":"[(600,105),(965,164),(990,531),(613,539)]"}' \
http://10.255.198.101:5000/add_source
