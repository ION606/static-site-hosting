all: build run

build:
	docker build -t static-sites .

run:
	docker run -d -p 5121:5121 --name static_sites static-sites

stop:
	docker stop static_sites || true

clean: stop
	docker rm static_sites
