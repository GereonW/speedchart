FROM python:3.8-buster
LABEL "authors"="Florian Heinle, David Gereon Wolf"
RUN ln -sf /usr/share/zoneinfo/Europe/Berlin /etc/localtime
WORKDIR /
RUN mkdir /data && apt-get update -q && apt-get install -y rrdtool && pip3 install requests speedtest-cli python-dateutil Pillow && fc-cache && apt-get clean
COPY measure.py /measure.py
CMD python3 ./measure.py
