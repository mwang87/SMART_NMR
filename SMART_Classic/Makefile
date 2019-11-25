create_dockerhub:
	docker pull calclavia/smart:cli

interactive:
	docker run -it -v "/home/mingxun/SourceCode/SMART_NMR/SMART_Classic/out:/out" --entrypoint /bin/bash calclavia/smart:cli 

cli:
	docker run -it calclavia/smart:cli -h 

test_data:
	python ./SMART.py ./input/XC817.csv output/test.npy
