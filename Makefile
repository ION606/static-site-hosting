all: run

run:
	nohup python app.py > output.log 2>&1 & echo $$! > app.pid

stop:
	@if [ -s app.pid ]; then \
		kill -9 $$(cat app.pid) && rm -f app.pid; \
	else \
		echo "No running process found."; \
	fi

restart: stop run

logs:
	tail -f output.log

clean: stop
	rm -f output.log app.pid

reset: clean
	rm -rf instance
	rm -rf sites