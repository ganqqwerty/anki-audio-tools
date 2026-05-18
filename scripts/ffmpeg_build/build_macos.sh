#!/usr/bin/env bash
set -euo pipefail

target="${1:-current}"
case "$target" in
  macos-arm64)
    arch="arm64"
    min_version="11.0"
    host_arg=""
    x86asm_arg=""
    ;;
  macos-x86_64)
    arch="x86_64"
    min_version="10.13"
    host_arg="--host=x86_64-apple-darwin"
    x86asm_arg="--disable-x86asm"
    ;;
  *)
    echo "usage: $0 macos-arm64|macos-x86_64" >&2
    exit 2
    ;;
esac

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
    CFLAGS="-O2 -arch $arch -mmacosx-version-min=$min_version" \
      ./configure \
        --disable-shared \
        --enable-static \
        --disable-frontend \
        --prefix="$lame_build/prefix" \
        ${host_arg:+"$host_arg"}
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
      --cc=clang \
      --arch="$arch" \
      --target-os=darwin \
      ${x86asm_arg:+"$x86asm_arg"} \
      --extra-cflags="-O2 -arch $arch -mmacosx-version-min=$min_version -I$lame_build/ffmpeg-include" \
      --extra-ldflags="-arch $arch -mmacosx-version-min=$min_version -L$lame_build/libmp3lame/.libs" \
      --extra-libs="-lm" \
      --enable-static \
      --disable-shared \
      --disable-autodetect \
      --disable-everything \
      --disable-doc \
      --disable-debug \
      --disable-ffplay \
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
    make -j"$(sysctl -n hw.ncpu)" ffmpeg ffprobe
  )
}

install_outputs() {
  mkdir -p "$output_dir"
  cp "$ffmpeg_build/ffmpeg" "$output_dir/ffmpeg"
  cp "$ffmpeg_build/ffprobe" "$output_dir/ffprobe"
  chmod 755 "$output_dir/ffmpeg" "$output_dir/ffprobe"
  codesign --force --sign - "$output_dir/ffmpeg"
  codesign --force --sign - "$output_dir/ffprobe"
}

verify_outputs() {
  "$output_dir/ffmpeg" -version
  "$output_dir/ffprobe" -version
  file "$output_dir/ffmpeg"
  file "$output_dir/ffprobe"
  otool -L "$output_dir/ffmpeg"
  otool -L "$output_dir/ffprobe"
  codesign -dv "$output_dir/ffmpeg" || true
  codesign -dv "$output_dir/ffprobe" || true
  xattr -l "$output_dir/ffmpeg" || true
  xattr -l "$output_dir/ffprobe" || true
}

download_if_missing "$lame_url" "$lame_archive"
download_if_missing "$ffmpeg_url" "$ffmpeg_archive"
verify_sha256 "$lame_archive" "$lame_sha"
verify_sha256 "$ffmpeg_archive" "$ffmpeg_sha"
build_lame
build_ffmpeg
install_outputs
verify_outputs
