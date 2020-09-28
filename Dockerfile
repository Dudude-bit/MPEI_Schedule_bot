FROM ubuntu:20.04

WORKDIR /home/mpei_bot

COPY ./ /home/mpei_bot

RUN apt-get -y update
RUN apt-get -y install git
RUN apt-get -y install python3
RUN apt-get -y install python3-pip
RUN pip3 install -r /home/mpei_bot/requirements.txt

CMD ["python3", "main.py"]