all: build run

build:
	docker build -t static-sites .

run:
	docker run -p 5121:5121 static-sites -d
