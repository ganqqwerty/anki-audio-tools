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

`wheels.lock.json` is the source of truth for exact filenames, download URLs,
sizes, SHA-256 digests, and wheel platform tags. Recreate or verify this
directory through the dev runner:

```bash
python3 scripts/dev.py vendor-wheels download --prune
python3 scripts/dev.py vendor-wheels verify
```

Release builds fail if the source-tree wheel files or the final `.ankiaddon`
archive do not match the lock.
