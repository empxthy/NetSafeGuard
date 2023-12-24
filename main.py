#!/usr/bin/python

# Coding: UTF-8
# Name: NetSafeGuard
# Author: AlexEmployed
# Version: 1.0.0
# License: GPL-3.0 version
# Copyright: alexemployed 2023
# Github: https://github.com/alexemployed
# Language: Python

# Imports
import configparser
import subprocess
import os
import re
import sys
import requests
import shutil
from collections import namedtuple

# Version
_version = "1.2.0"

# Colors
_black = "\033[0;30m"
_red = "\033[0;31m"
_green = "\033[0;32m"
_brown = "\033[0;33m"
_blue = "\033[0;34m"
_yellow = "\033[1;33m"
_purple = "\033[0;35m"
_cyan = "\033[0;36m"
_white="\033[0;37m"
_lightGray = "\033[0;37m"
_darkGray = "\033[1;30m"
_lightRed = "\033[1;31m"
_lightGreen = "\033[1;32m"
_lightBlue = "\033[1;34m"
_lightPurple = "\033[1;35m"
_lightCyan = "\033[1;36m"
_lightWhite = "\033[1;37m"


# Logo

def startup():
    print(f""" {_red}
    ███╗   ██╗███████╗████████╗███████╗ █████╗ ███████╗███████╗ ██████╗ ██╗   ██╗ █████╗ ██████╗ ██████╗ 
    ████╗  ██║██╔════╝╚══██╔══╝██╔════╝██╔══██╗██╔════╝██╔════╝██╔════╝ ██║   ██║██╔══██╗██╔══██╗██╔══██╗
    ██╔██╗ ██║█████╗     ██║   ███████╗███████║█████╗  █████╗  ██║  ███╗██║   ██║███████║██████╔╝██║  ██║
    ██║╚██╗██║██╔══╝     ██║   ╚════██║██╔══██║██╔══╝  ██╔══╝  ██║   ██║██║   ██║██╔══██║██╔══██╗██║  ██║
    ██║ ╚████║███████╗   ██║   ███████║██║  ██║██║     ███████╗╚██████╔╝╚██████╔╝██║  ██║██║  ██║██████╔╝
    ╚═╝  ╚═══╝╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚══════╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ 

    {_cyan}[+]CREATOR: {_white}https://github.com/alexemployed                                            {_cyan}Version:{_white} {_version}
                                                                                                        """)

# Check Update
def check_update(repo_owner, repo_name, current_version):
    print(f"{_yellow}[!]{_white}Checking for updates...")

    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"

    try:
        response = requests.get(api_url)
        response.raise_for_status()

        latest_release = response.json()
        latest_version = latest_release["tag_name"]

        if current_version >= latest_version:
            print(f"{_green}[+]{_white}Your software is up to date (version {current_version}).")
        else:
            print(f"{_red}[-]{_white}A new version ({latest_version}) is available. Please update your software.")
            upt = str(input(f"{_yellow}[!]{_white}Update now?: [{_green}y{_white}/{_red}n{_white}]\n{_yellow}[?]{_white}Y/N: "))
            clone_path = os.path.join(os.path.expanduser('~'), 'Desktop')
            if upt == "y":
                try:
                    shutil.rmtree(clone_path)
                    subprocess.run(["git", "clone", "https://github.com/alexemployed/NetSafeGuard.git", clone_path], check=True)
                    print(f"{_green}[+]{_white}Repository cloned successfully!")
                except subprocess.CalledProcessError as e:
                    print(f"Error: {_red}{e}{_white}")
            
            if upt == "n":
                print(f"{_red}[-]{_white}Update cancelled by user!")
                sys.exit(1)
    
    except requests.exceptions.RequestException as e:
        print(f"{_red}[-]{_white}Error: {e}")
        print(f"Response content: {response.content}")

# Privalages
    
def check_root():
    ret = 0
    if os.geteuid != 0:
        msg = "[sudo] password for %u: "
        ret = subprocess.check_call("sudo -v -p '%s'" %msg, shell=True)
    return ret

def check_admin():
    try:
        subprocess.check_call(["net", "session"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError:
        return False

# Windows Wifi

def get_windows_saved_ssids():
    output = subprocess.check_output("netsh wlan show profiles").decode()
    ssids = []
    profiles = re.findall(r"Entire user profile\s(.*)", output)
    for profile in profiles:
        ssid = profile.strip().strip(":").strip()
        ssids.append(ssid)
    return ssids

def get_windows_saved_wifi_passwords(verbose=1):
    ssids = get_windows_saved_ssids()
    Profile = namedtuple("Profile", ["ssid", "ciphers", "key"])
    profiles = []
    for ssid in ssids:
        ssid_details = subprocess.check_output(f"""netsh wlan show profile "{ssid}" key=clear""").decode()
        ciphers = re.findall(r"Cipher\s(.*)", ssid_details)
        ciphers = "/".join([c.strip().strip(":").strip() for c in ciphers])
        key = re.findall(r"Key Content\s(.*)", ssid_details)
        try:
            key = key[0].strip().strip(":").strip()
        except IndexError:
            key = "None"
        profile = Profile(ssid=ssid, ciphers=ciphers, key=key)
        if verbose >= 1:
            print_windows_profile(profile)
        profiles.append(profile)
    return profiles

def print_windows_profile(profile):
    print(f"{profile.ssid:25}{profile.ciphers:15}{profile.key:50}")

def print_windows_profiles(verbose):
    print("SSID                     CIPHER(S)      KEY")
    get_windows_saved_wifi_passwords(verbose)

# Linux Wifi

def get_linux_saved_wifi_passwords(verbose=1):   
    network_connections_path = "/etc/NetworkManager/system-connections/"
    fields = ["ssid", "auth-alg", "key-mgmt", "psk"]
    Profile = namedtuple("Profile", [f.replace("-", "_") for f in fields])
    profiles = []
    for file in os.listdir(network_connections_path):
        data = { k.replace("-", "_"): None for k in fields }
        config = configparser.ConfigParser()
        config.read(os.path.join(network_connections_path, file))
        for _, section in config.items():
            for k, v in section.items():
                if k in fields:
                    data[k.replace("-", "_")] = v
        profile = Profile(**data)
        if verbose >= 1:
            print_linux_profile(profile)
        profiles.append(profile)
    return profiles

def print_linux_profile(profile):
    print(f"{str(profile.ssid):25}{str(profile.auth_alg):5}{str(profile.key_mgmt):10}{str(profile.psk):50}")

def print_linux_profiles(verbose):
    print("SSID                     AUTH KEY-MGMT  PSK")
    get_linux_saved_wifi_passwords(verbose)
    
    
def print_profiles(verbose=1):
    if os.name == "nt":
        print_windows_profiles(verbose)
    elif os.name == "posix":
        print_linux_profiles(verbose)
    else:
        raise NotImplemented("Program runs only on Windows and POSIX systems!")
    
    
if __name__ == "__main__":
    startup()
    if os.name == 'posix':
        check_root()
    elif os.name == 'nt':
        check_admin()
    else:
        sys.exit(1)
    check_update("alexemployed", "NetSafeGuard", _version)
    print_profiles()