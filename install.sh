#!/bin/sh

if [ $(id -u) -ne 0 ]
  then echo "Please run as root"
  exit
fi

sudo rm /usr/share/X11/xkb/symbols/typo-birman-*
sudo cp symbols/* /usr/share/X11/xkb/symbols/

# Edit /usr/share/X11/xkb/rules/evdev.lst

sudo sed -i -E 's/\s*typo-birman.*//g' /usr/share/X11/xkb/rules/evdev.lst
sudo sed -i -E 's/(! layout)/\1\n  typo-birman-en         English (Typographic by Ilya Birman)\n  typo-birman-ru         Russian (Typographic by Ilya Birman)/g' /usr/share/X11/xkb/rules/evdev.lst

# Edit /usr/share/X11/xkb/rules/evdev.xml

sudo awk '/<\/layoutList>/ { system ( "cat ./rules/envdev.xml" ) } { print; }' /usr/share/X11/xkb/rules/evdev.xml >> /tmp/evdev.xml
sudo rm /usr/share/X11/xkb/rules/evdev.xml
sudo mv /tmp/evdev.xml /usr/share/X11/xkb/rules/evdev.xml

# Enable AltGr
gsettings set org.gnome.desktop.input-sources xkb-options "['lv3:ralt_switch']"

# Enable keyboard layouts
gsettings set org.gnome.desktop.input-sources sources "[('xkb', 'typo-birman-en'), ('xkb', 'typo-birman-ru')]"

# Show further instructions
echo "Please log out and log in again to activate the new keyboard layouts."
