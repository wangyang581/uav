docker run --name visdrone \
	--shm-size=16g \
	--gpus='device=0' \
	--log-opt max-size=100m \
	--log-opt max-file=2 \
	--network=host \
	-ti \
	-v $(pwd):/visdrone \
	-w /visdrone \
	opencv_yolov8:5.0 \
	/bin/bash
