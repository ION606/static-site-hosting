FROM python:3.9-slim

# disable buffering to show logs in real time
ENV PYTHONUNBUFFERED=1

# set working directory to /app
WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5121

CMD ["python", "app.py"]
