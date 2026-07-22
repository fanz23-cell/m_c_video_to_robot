# venv Setup

Run:

```bash
./scripts/bootstrap_venvs.sh
```

The script creates:

```text
.venv-tools
.venv-gvhmr
.venv-gmr
.venv-isaac
```

Every install is invoked as:

```bash
./.venv-xxx/bin/python -m pip install ...
```

The scripts do not depend on activating shells. If `python3-venv` is missing, install it with:

```bash
sudo apt install python3-venv
```

GVHMR pins CUDA PyTorch wheels in its upstream requirements. If that install fails, check your Python version, driver, CUDA wheel compatibility, and network access.

If your system `python3` is not Python 3.10, install a Python 3.10 interpreter with venv support and run:

```bash
PYTHON_GVHMR=python3.10 ./scripts/bootstrap_venvs.sh
```

If `.venv-gvhmr` was already created with a different Python version, the bootstrap script recreates that venv with the requested interpreter.

GVHMR depends on the legacy `chumpy` package. The bootstrap script installs it with `--no-build-isolation` before applying the official upstream requirements because the package's old build script expects `pip` to be importable during setup.
