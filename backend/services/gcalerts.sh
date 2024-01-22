#!/bin/sh
if [ -z "$1" ]; then
	echo "usage: $0 [start|stop|status]"
	exit
fi
sudo systemctl $1 gcalerts
