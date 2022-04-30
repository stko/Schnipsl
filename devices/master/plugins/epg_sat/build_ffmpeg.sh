sudo apt-get update -qq && sudo apt-get -y install \
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
sudo apt -y install libunistring-dev libaom-dev libdav1d-dev
mkdir -p ~/ffmpeg_sources ~/bin

# compiles ffmpeg without any special codec, as it is only used for satip filtering

cd ~/ffmpeg_sources && \
wget -O ffmpeg-5.0.1.tar.bz2 https://ffmpeg.org/releases/ffmpeg-5.0.1.tar.bz2 && \
tar xjvf ffmpeg-5.0.1.tar.bz2 && \
cd ffmpeg-5.0.1 && \
PATH="$HOME/bin:$PATH" PKG_CONFIG_PATH="$HOME/ffmpeg_build/lib/pkgconfig" ./configure \
  --prefix="$HOME/ffmpeg_build" \
  --pkg-config-flags="--static" \
  --extra-cflags="-I$HOME/ffmpeg_build/include" \
  --extra-ldflags="-L$HOME/ffmpeg_build/lib" \
  --extra-libs="-lpthread -lm" \
  --ld="g++" \
  --bindir="$HOME/bin" \
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

