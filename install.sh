#!/bin/bash

BASE=$(dirname "$0")

sudo rm -f /usr/share/X11/xkb/symbols/typo-birman-*
sudo cp $BASE/symbols/* /usr/share/X11/xkb/symbols/

# Edit /usr/share/X11/xkb/rules/evdev.lst

sudo sed -i -E 's/\s*typo-birman.*//g' /usr/share/X11/xkb/rules/evdev.lst
sudo sed -i -E 's/(! layout)/\1\n  typo-birman-en         English (Typographic by Ilya Birman)\n  typo-birman-ru         Russian (Typographic by Ilya Birman)/g' /usr/share/X11/xkb/rules/evdev.lst

# Edit /usr/share/X11/xkb/rules/evdev.xml

sudo awk "/<\/layoutList>/ { system ( \"cat $BASE/rules/envdev.xml\" ) } { print; }" /usr/share/X11/xkb/rules/evdev.xml >> /tmp/evdev.xml
sudo rm /usr/share/X11/xkb/rules/evdev.xml
sudo mv /tmp/evdev.xml /usr/share/X11/xkb/rules/evdev.xml

# Enable AltGr
gsettings set org.gnome.desktop.input-sources xkb-options "['lv3:ralt_switch']"

# Enable keyboard layouts
gsettings set org.gnome.desktop.input-sources sources "[('xkb', 'typo-birman-en'), ('xkb', 'typo-birman-ru')]"

# Show further instructions
echo -e "\e[32mDone! Please log out and log in again to activate the new keyboard layouts.\e[0m"
echo
# Set input switching to Shift+Alt (like in Windows)
read -r -p "By the way, do you want to toggle keyboard layouts with Shift+Alt? (default=yes)" response
echo
response=${response,,}
if [[ $response =~ ^(yes|y| ) ]] | [ -z $response ]; then
    gsettings set org.gnome.desktop.wm.keybindings switch-input-source "['<Shift>Alt_L']"
    gsettings set org.gnome.desktop.wm.keybindings switch-input-source-backward "['<Alt>Shift_L']"
fi

