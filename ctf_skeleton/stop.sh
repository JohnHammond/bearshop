#!/bin/bash

ps aux|grep "server.py"|cut -d" " -f6| while read line; do sudo kill -9 $line; done
ps aux|grep "server.py"|cut -d" " -f7| while read line; do sudo kill -9 $line; done
