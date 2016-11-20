#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Installation script"""
import getpass
from subprocess import check_call, Popen

WPA_SUPPLICANT_CONF = "/etc/wpa_supplicant/wpa_supplicant.conf"
WIFI_CONFIG = """
network={
  ssid="{}"
  psk="{}"
  proto=RSN
  key_mgmt=WPA-PSK
  pairwise=CCMP
  auth_alg=OPEN
}
"""

def read_output(*args):
    """Reads the whole output of *args shell command"""
    proc = Popen(args)
    proc.wait()
    stdoutdata, stderrdata = proc.communicate()
    return stdoutdata

def ask_password():
    """Asks for password twice and returns both inputs"""
    psk1 = getpass.getpass("Password: ")
    psk2 = getpass.getpass("Retype password: ")
    return psk1, psk2

def main():
    """Main process of this script"""
    if getpass.getuser() != "root":
        raise RuntimeError("This script should be executed as root")

    check_call("apt-get update".split(" "))
    check_call("apt-get upgrade".split(" "))
    check_call("apt-get install -qq rpi-update python-picamera python-tornado "
               "python-opencv python-pil".split(" "))

    ssid = input("What's your WIFI SSID: ")

    with open(WPA_SUPPLICANT_CONF) as wpa_supplicant:
        content = wpa_supplicant.read()

    if '"'+ssid+'"' not in content:
        psk1, psk2 = ask_password()
        while psk1 != psk2:
            print "Password missmatch. Try again."
            psk1, psk2 = ask_password()

        with open(WPA_SUPPLICANT_CONF, "a") as wpa_supplicant:
            wpa_supplicant.write(WIFI_CONFIG.format(ssid, psk1))
    else:
        print "Skipping SSID, it is really configured in wpa_supplicant.conf"

if __name__ == "__main__":
    main()
