FROM python:3

RUN mkdir -p /var/imam
WORKDIR /var/imam
COPY ./ /var/imam

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
RUN pip install git+https://github.com/Pycord-Development/pycord.git

RUN apt-get update
RUN apt-get install -y ffmpeg

ENTRYPOINT python /var/imam/bot.py
