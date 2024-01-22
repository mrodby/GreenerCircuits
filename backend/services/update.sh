#!/bin/sh
sudo cp *.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo cp *.sh /usr/local/bin/
