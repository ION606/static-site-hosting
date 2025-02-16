all: build run

build:
	docker build -t static-sites .

run:
	docker run -d -p 5121:5121 \
		-v $(PWD)/templates:/app/templates \
		-v $(PWD)/static:/app/static \
		-v $(PWD)/sites:/app/sites \
		-v $(PWD)/db.sqlite:/app/db.sqlite \
		--name static_sites static-sites

stop:
	docker stop static_sites || true

clean: stop
	docker rm static_sites || true
