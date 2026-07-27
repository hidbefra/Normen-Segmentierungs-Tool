#!/usr/bin/env bash
set -e

ENV_NAME=".venv"
python3 -m venv "$ENV_NAME"
source "$ENV_NAME/bin/activate"
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e .[dev]
pre-commit install || true
