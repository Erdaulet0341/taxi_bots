FROM python:3.9
WORKDIR /code
COPY requirements.txt .
RUN pip3 install -r requirements.txt
COPY . .
RUN mkdir -p /code/logs && chmod 777 /code/logs
RUN chmod +x ./start.sh
CMD ["./start.sh"]
