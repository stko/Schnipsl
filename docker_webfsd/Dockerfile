ARG ALPHINE_VERSION=3.10
FROM alpine:$ALPHINE_VERSION AS builder
ARG WEBFS_VERSION=1.21
RUN apk update && apk add build-base mailcap
RUN wget https://www.kraxel.org/releases/webfs/webfs-$WEBFS_VERSION.tar.gz -O - | tar xzf - \
 && cd webfs-$WEBFS_VERSION && make install && cd .. && rm -r webfs-$WEBFS_VERSION

FROM alpine:$ALPHINE_VERSION
COPY --from=builder /etc/mime.types /etc/mime.types
COPY --from=builder /usr/local/bin/webfsd /usr/local/bin/webfsd
EXPOSE 80
CMD /usr/local/bin/webfsd -p 80 -d -r /srv
