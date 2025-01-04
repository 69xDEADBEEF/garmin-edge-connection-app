#!/bin/bash

# System Preparation Script
sudo apt-get update
sudo apt-get install -y \
    python3-pip \
    python3-pyqt5 \
    python3-dbus \
    python3-pyudev \
    bluez \
    blueman \
    udisks2 \
    devscripts \
    debhelper

# Install Python dependencies
pip3 install \
    pyudev \
    PyQt5 \
    dbus-python \
    python-mount

# Build Debian Package
./build-garmin-package.sh

# Install the package
sudo dpkg -i garmin-connection-app.deb
sudo apt-get install -f  # Fix any dependency issues
