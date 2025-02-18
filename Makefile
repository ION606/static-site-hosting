all: run

run:
	docker compose up --build -d

stop:
	docker compose down -v

restart: stop run

logs:
	docker compose logs -f

clean: stop
	rm -f output.log app.pid

reset: clean
	rm -rf instance
	rm -rf sites