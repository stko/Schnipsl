FROM debian:latest AS builder

WORKDIR /app
ADD webapp ./webapp

RUN apt-get update && \
    apt-get install -y openssl npm && \
     mkdir -p devices/master && \
    openssl req -newkey rsa:2048 -new -nodes -x509 \
    -days 3650 -subj "/C=DE/ST=Brake/L=lower Saxony/O=stko/OU=IT Department/CN=koehlers.de" \
    -keyout devices/master/key.pem -out devices/master/server.pem && \
    cd webapp && \
    npm install && \
    npm run build && \
    ls







FROM python:3

WORKDIR /app/webapp
COPY --from=builder /app/webapp/dist ./dist

WORKDIR /app/devices/master
COPY devices/master/*.py ./
COPY --from=builder /app/devices/master/*.pem ./
ADD devices/master/plugins ./plugins
ADD devices/common ../common

WORKDIR /app
COPY installdockers.sh /tmp/installdockers.sh
RUN chmod +x /tmp/installdockers.sh
RUN /usr/local/bin/python -m pip install --upgrade pip
RUN bash -c "/tmp/installdockers.sh"

WORKDIR /app/devices/master

CMD [ "python3", "./schnipsl.py" , "-s" ]

EXPOSE 8000