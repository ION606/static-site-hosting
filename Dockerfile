FROM python:3.9-slim

RUN addgroup --gid 1000 appuser && \
	adduser --uid 1000 --gid 1000 --disabled-password --gecos "" appuser && \
	mkdir -p /app/sites && \
	chown -R appuser:appuser /app/sites

# disable buffering to show logs in real time
ENV PYTHONUNBUFFERED=1

# set working directory to /app
WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5121

USER appuser

CMD ["python", "run.py"]
