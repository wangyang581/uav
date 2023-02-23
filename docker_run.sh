docker run --name face_server \
	--shm-size=8g \
	--gpus='"device=0"' \
	--network=host \
	-p 5000:5000 \
	-v $(pwd):/workspace/face_server \
	-w /workspace/face_server \
	-ti \
	--log-opt max-size=100m \
	--log-opt max-file=2 \
	engine_opencv:1.0 \
	python3 flask_server.py
