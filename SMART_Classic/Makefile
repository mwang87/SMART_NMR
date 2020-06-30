create_dockerhub:
	docker pull calclavia/smart:cli

interactive:
	docker run -it -v "/home/mingxun/SourceCode/SMART_NMR/SMART_Classic/out:/out" --entrypoint /bin/bash calclavia/smart:cli 

cli:
	docker run -it calclavia/smart:cli -h 

test_data:
	python ./SMART.py ./input/XC817.csv output/test.npy

download_2_1_db:
	wget --output-document="DB.json" https://www.dropbox.com/s/uge3xn394fw25vp/DB_06282020_SM2.1%28100K%29.json?dl=1
	
download_2_0_db:
	wget --output-document="DB.json" https://www.dropbox.com/s/hki1tcpyipcr124/DB_SMART_2_0_MW.json?dl=1

download_db:
	wget --output-document="DB.json" https://www.dropbox.com/s/mj9wp1nqw1ec4wf/DB_200220_MW2.json?dl=1

