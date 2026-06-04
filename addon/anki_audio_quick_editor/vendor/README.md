# Vendored Python Wheels

This directory stores compressed wheels for runtime Python dependencies that
Anki users cannot install with pip.

Current wheel set:

- `praat-parselmouth==0.4.7`
- `numpy==2.4.6`

Wheels are grouped by the add-on's supported platform keys:

- `macos-arm64`
- `macos-x86_64`
- `windows-x86_64`

At startup, `vendor_runtime.activate_vendor()` extracts only the current
platform's wheels into `user_files/python_vendor/` and prepends that extracted
site-packages directory to `sys.path`.
