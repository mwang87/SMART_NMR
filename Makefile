build:
	docker build -t nmr_smart . 

build-classic:
	docker build -t nmr_smart_classic -f classic.Dockerfile .


# Tests
interactive:
	docker run -it nmr_smart /bin/bash

interactive-classic:
	docker run -it nmr_smart_classic /bin/bash



#Docker Compose
server-compose-interactive:
	docker-compose build
	docker-compose up

server-compose:
	docker-compose build
	docker-compose up -d

server-compose-production-interactive:
	docker-compose build
	docker-compose -f docker-compose.yml -f docker-compose-production.yml up

server-compose-production:
	docker-compose build
	docker-compose -f docker-compose.yml -f docker-compose-production.yml up -d


attach:
	docker exec -it smart_nmr_smartfp-tf-server_1 /bin/bash

attach-classic:
	docker exec -it smartclassic-worker /bin/bash


# ACT Testing
test-production:
	act -P ubuntu-latest=nektos/act-environments-ubuntu:18.04 -b