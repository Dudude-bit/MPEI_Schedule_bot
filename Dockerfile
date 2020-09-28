FROM alpine

COPY ./ /home/mpei_bot

RUN apk add git && apk add python3