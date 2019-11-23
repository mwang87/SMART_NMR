build:
	docker build -t nmr_smart . 


# Tests
interactive:
	docker run -it nmr_smart /bin/bash




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