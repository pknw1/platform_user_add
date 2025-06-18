FROM python:3-alpine3.22
RUN mkdir /config
ADD requirements.txt requirements.txt
RUN pip install -r requirements.txt
ADD notflix_adduser_service.py notflix_adduser_service.py
ENTRYPOINT ["python", "notflix_adduser_service.py"]
