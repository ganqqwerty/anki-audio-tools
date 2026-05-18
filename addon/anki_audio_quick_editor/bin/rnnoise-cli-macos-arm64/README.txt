RNNoise CLI bundle for macOS arm64.

Usage:
  ./bin/rnnoise-cli --version
  ./bin/rnnoise-cli denoise --input input.s16le --output output.s16le --overwrite --json

The CLI processes raw 48 kHz mono signed 16-bit little-endian PCM. Audio Quick
Editor uses ffmpeg to prepare that input and encode the denoised output.
