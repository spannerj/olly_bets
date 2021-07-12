#!/bin/bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m pip install --upgrade pip
source env
python olly.py