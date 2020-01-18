# Python support can be specified down to the minor or micro version
# (e.g. 3.6 or 3.6.3).
# OS Support also exists for jessie & stretch (slim and full).
# See https://hub.docker.com/r/library/python/ for all supported Python
# tags from Docker Hub.
# FROM python:alpine
FROM python:3.6-alpine3.9

LABEL Name=music-share-bot Version=0.0.1
EXPOSE 3000

WORKDIR /app
ADD . /app

RUN apk update && apk add gcc libc-dev make git libffi-dev openssl-dev python3-dev libxml2-dev libxslt-dev jpeg-dev g++

# Using pip:
RUN python3 -m pip install -r requirements.txt
CMD ["python3", "./server.py"]

# Using pipenv:
#RUN python3 -m pip install pipenv
#RUN pipenv install --ignore-pipfile
#CMD ["pipenv", "run", "python3", "-m", "music-share-bot"]

# Using miniconda (make sure to replace 'myenv' w/ your environment name):
#RUN conda env create -f environment.yml
#CMD /bin/bash -c "source activate myenv && python3 -m music-share-bot"
