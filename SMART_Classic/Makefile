create_dockerhub:
	docker pull calclavia/smart:cli

interactive:
	docker run -it -v "/home/mingxun/SourceCode/SMART_NMR/SMART_Classic/out:/out" --entrypoint /bin/bash calclavia/smart:cli 

cli:
	docker run -it calclavia/smart:cli -h 

test_data:
	python ./SMART.py ./input/XC817.csv output/test.npy

download_2_0_db:
	wget --output-document="DB.json" https://www.dropbox.com/s/slifhv3sqvkoq6s/lib_old.json?dl=1

download_db:
	wget --output-document="DB.json" https://www.dropbox.com/s/mj9wp1nqw1ec4wf/DB_200220_MW2.json?dl=1

