docker run --name face_server \
	--shm-size=16g \
	--gpus='device=0' \
	--log-opt max-size=100m \
	--log-opt max-file=2 \
	--network=host \
	-ti \
	-p 5000:5000 \
	-v $(pwd):/workspace/face_server \
	-w /workspace/face_server \
	engine_server:1.0 \
	bash start_server.sh
