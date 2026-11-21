FROM python:3.12-slim
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY *.py /app/
WORKDIR /app
ENTRYPOINT ["python", "-u"]
