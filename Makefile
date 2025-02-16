all: run

run:
	nohup .venv/bin/python app.py > output.log 2>&1 & echo $! > app.pid

stop:
	kill -9 $(cat app.pid) || true
	rm -f app.pid

restart: stop run

logs:
	tail -f output.log

clean: stop
	rm -f output.log

