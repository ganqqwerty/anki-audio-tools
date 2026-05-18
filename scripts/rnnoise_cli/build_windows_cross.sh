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
source_url="https://github.com/xiph/rnnoise/releases/download/v0.2/rnnoise-0.2.tar.gz"
source_sha="90fce4b00b9ff24c08dbfe31b82ffd43bae383d85c5535676d28b0a2b11c0d37"
source_archive="$root/.release-assets/sources/rnnoise-0.2.tar.gz"
build_dir="$root/.release-assets/build/rnnoise-$target"
output="$root/.release-assets/bin/$target/rnnoise-cli.exe"

mkdir -p "$(dirname "$source_archive")" "$(dirname "$output")"
if [[ ! -f "$source_archive" ]]; then
  curl -fL --retry 3 -o "$source_archive" "$source_url"
fi
actual_sha="$(shasum -a 256 "$source_archive" | awk '{print $1}')"
if [[ "$actual_sha" != "$source_sha" ]]; then
  echo "rnnoise source checksum mismatch: expected $source_sha, got $actual_sha" >&2
  exit 1
fi

rm -rf "$build_dir"
mkdir -p "$build_dir"
tar -xzf "$source_archive" -C "$build_dir" --strip-components=1

cat > "$build_dir/src/os_support.h" <<'EOF'
#ifndef OS_SUPPORT_H
#define OS_SUPPORT_H
#include "common.h"
#define OPUS_CLEAR(dst, n) RNN_CLEAR((dst), (n))
#endif
EOF

(
  cd "$build_dir"
  CC=x86_64-w64-mingw32-gcc \
    ./configure --host=x86_64-w64-mingw32 --disable-shared --enable-static --prefix="$build_dir/install"
  make -j"$(sysctl -n hw.ncpu)"
  x86_64-w64-mingw32-gcc -O2 \
    -Iinclude -Isrc "$root/scripts/rnnoise_cli/rnnoise_cli.c" \
    .libs/librnnoise.a -static -lm -o "$output"
)

file "$output"
x86_64-w64-mingw32-objdump -p "$output" | sed -n '/DLL Name/p'
