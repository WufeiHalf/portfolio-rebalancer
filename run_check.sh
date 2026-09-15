#!/bin/bash
cd "$(dirname "$0")"
UV_DEFAULT_INDEX="https://pypi.tuna.tsinghua.edu.cn/simple" \
  exec uv run --quiet --with yfinance --with requests --no-project python check.py
