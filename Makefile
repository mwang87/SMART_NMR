build:
	docker build -t nmr_smart . 

#Docker Compose
server-compose-interactive:
	docker-compose build
	docker-compose up

server-compose:
	docker-compose build
	docker-compose up -d