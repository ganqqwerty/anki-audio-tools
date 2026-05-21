# DPDFNet Lite Build Source

This directory vendors the small DPDFNet Lite CLI source used only by the
release build scripts. It is adapted from
https://github.com/ceva-ip/DPDFNet/tree/main/package/src/dpdfnet_lite and is
distributed under Apache-2.0; see `LICENSE`.

The `dpdfnet4.tflite` model is not committed here. `build_lite.py` downloads
the locked model artifact and verifies its size and SHA-256 before bundling it
with PyInstaller.
