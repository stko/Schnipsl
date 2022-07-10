FROM debian:buster AS builder

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

WORKDIR /ffmpeg

RUN apt-get update -qq && apt-get -y install \
  autoconf \
  automake \
  build-essential \
  cmake \
  git-core \
  libass-dev \
  libfreetype6-dev \
  libgnutls28-dev \
  libmp3lame-dev \
  libtool \
  libvorbis-dev \
  meson \
  ninja-build \
  pkg-config \
  texinfo \
  wget \
  yasm \
  zlib1g-dev
#RUN apt -y install libunistring-dev libaom-dev libdav1d-dev
RUN apt -y install libunistring-dev libaom-dev
RUN mkdir ffmpeg_sources bin

# compiles ffmpeg without any special codec, as it is only used for satip filtering

RUN cd ffmpeg_sources && \
wget -O ffmpeg-5.0.1.tar.bz2 https://ffmpeg.org/releases/ffmpeg-5.0.1.tar.bz2 && \
tar xjvf ffmpeg-5.0.1.tar.bz2 && \
cd ffmpeg-5.0.1 && \
PATH="$HOME/bin:$PATH" PKG_CONFIG_PATH="$HOME/ffmpeg_build/lib/pkgconfig" ./configure \
  --prefix="ffmpeg_build" \
  --pkg-config-flags="--static" \
  --extra-cflags="-Iffmpeg_build/include" \
  --extra-ldflags="-Lffmpeg_build/lib" \
  --extra-libs="-lpthread -lm" \
  --ld="g++" \
  --bindir="bin" \
  --enable-gpl \
  --enable-gnutls \
  --enable-libass \
  --enable-libfreetype \
  --enable-libmp3lame \
  --enable-libvorbis \
  --enable-nonfree && \
PATH="$HOME/bin:$PATH" make && \
hash -r
# make install && \





#FROM python:3
FROM python:3-buster

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
RUN /usr/local/bin/python3 -m pip install --upgrade pip
RUN bash -c "/tmp/installdockers.sh"

# copy the self compiled ffmeg AFTER all installers went through
WORKDIR /
COPY --from=builder /ffmpeg/ffmpeg_sources/ffmpeg-5.0.1/ffmpeg /usr/bin/

WORKDIR /app/devices/master

CMD [ "python3", "./schnipsl.py" , "-s" ]

EXPOSE 8000
