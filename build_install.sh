#!/bin/bash
desktop-file-validate dist/linux/usr/share/applications/smartodoo.desktop
sudo dpkg -r smartodoo && dpkg-deb --build dist/linux smartodoo.deb && sudo dpkg -i smartodoo.deb