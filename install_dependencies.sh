#!/bin/bash

apt-get -y update && apt-get -y install pip sqlite3
pip install passlib flask colorama image python-resize-image
