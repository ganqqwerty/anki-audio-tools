#!/usr/bin/env bash
set -euo pipefail

target="${1:-windows-x86_64}"
case "$target" in
  windows-x86_64) ;;
  *)
    echo "usage: $0 windows-x86_64" >&2
    exit 2
    ;;
esac

if ! command -v x86_64-w64-mingw32-gcc >/dev/null 2>&1; then
  echo "x86_64-w64-mingw32-gcc not found. Install Homebrew mingw-w64 or build on Windows." >&2
  exit 1
fi

root="$(cd "$(dirname "$0")/../.." && pwd)"
sources_dir="$root/.release-assets/sources"
build_root="$root/.release-assets/build"
output_dir="$root/.release-assets/bin/$target"

lame_url="https://downloads.sourceforge.net/project/lame/lame/3.100/lame-3.100.tar.gz"
lame_sha="ddfe36cab873794038ae2c1210557ad34857a4b6bdc515785d1da9e175b1da1e"
lame_archive="$sources_dir/lame-3.100.tar.gz"
lame_build="$build_root/lame-$target"

ffmpeg_url="https://ffmpeg.org/releases/ffmpeg-8.1.1.tar.xz"
ffmpeg_sha="b6863adde98898f42602017462871b5f6333e65aec803fdd7a6308639c52edf3"
ffmpeg_archive="$sources_dir/ffmpeg-8.1.1.tar.xz"
ffmpeg_build="$build_root/ffmpeg-$target"

download_if_missing() {
  local url="$1"
  local destination="$2"
  mkdir -p "$(dirname "$destination")"
  if [[ ! -f "$destination" ]]; then
    curl -fL --retry 3 -o "$destination" "$url"
  fi
}

verify_sha256() {
  local path="$1"
  local expected="$2"
  local actual
  actual="$(shasum -a 256 "$path" | awk '{print $1}')"
  if [[ "$actual" != "$expected" ]]; then
    echo "checksum mismatch for $path: expected $expected, got $actual" >&2
    exit 1
  fi
}

build_lame() {
  rm -rf "$lame_build"
  mkdir -p "$lame_build"
  tar -xzf "$lame_archive" -C "$lame_build" --strip-components=1
  (
    cd "$lame_build"
    CC=x86_64-w64-mingw32-gcc \
      AR=x86_64-w64-mingw32-ar \
      RANLIB=x86_64-w64-mingw32-ranlib \
      ./configure \
        --host=x86_64-w64-mingw32 \
        --disable-shared \
        --enable-static \
        --disable-frontend \
        --prefix="$lame_build/prefix"
    make -j"$(sysctl -n hw.ncpu)"
  )
  mkdir -p "$lame_build/ffmpeg-include/lame"
  cp "$lame_build/include/lame.h" "$lame_build/ffmpeg-include/lame/lame.h"
}

build_ffmpeg() {
  rm -rf "$ffmpeg_build"
  mkdir -p "$ffmpeg_build"
  tar -xJf "$ffmpeg_archive" -C "$ffmpeg_build" --strip-components=1
  (
    cd "$ffmpeg_build"
    ./configure \
      --prefix="$ffmpeg_build/install" \
      --arch=x86_64 \
      --target-os=mingw32 \
      --cross-prefix=x86_64-w64-mingw32- \
      --cc=x86_64-w64-mingw32-gcc \
      --disable-x86asm \
      --extra-cflags="-O2 -I$lame_build/ffmpeg-include" \
      --extra-ldflags="-static -L$lame_build/libmp3lame/.libs" \
      --extra-libs="-lm" \
      --enable-static \
      --disable-shared \
      --disable-autodetect \
      --disable-everything \
      --disable-doc \
      --disable-debug \
      --disable-ffplay \
      --disable-network \
      --enable-ffmpeg \
      --enable-ffprobe \
      --enable-protocol=file,pipe \
      --enable-demuxer=aac,flac,matroska,mov,mp3,ogg,wav \
      --enable-muxer=mp3,null,s16le,wav \
      --enable-decoder=aac,alac,flac,mp3,mp3float,opus,pcm_f32le,pcm_s16le,pcm_s24le,vorbis \
      --enable-encoder=libmp3lame,pcm_s16le \
      --enable-parser=aac,flac,mpegaudio,opus,vorbis \
      --enable-filter=anull,aresample,asetpts,atempo,atrim,concat,silencedetect,volume \
      --enable-libmp3lame
    make -j"$(sysctl -n hw.ncpu)" ffmpeg.exe ffprobe.exe
  )
}

install_outputs() {
  mkdir -p "$output_dir"
  cp "$ffmpeg_build/ffmpeg.exe" "$output_dir/ffmpeg.exe"
  cp "$ffmpeg_build/ffprobe.exe" "$output_dir/ffprobe.exe"
}

verify_outputs() {
  file "$output_dir/ffmpeg.exe"
  file "$output_dir/ffprobe.exe"
  x86_64-w64-mingw32-objdump -p "$output_dir/ffmpeg.exe" | sed -n '/DLL Name/p'
  x86_64-w64-mingw32-objdump -p "$output_dir/ffprobe.exe" | sed -n '/DLL Name/p'
}

download_if_missing "$lame_url" "$lame_archive"
download_if_missing "$ffmpeg_url" "$ffmpeg_archive"
verify_sha256 "$lame_archive" "$lame_sha"
verify_sha256 "$ffmpeg_archive" "$ffmpeg_sha"
build_lame
build_ffmpeg
install_outputs
verify_outputs
