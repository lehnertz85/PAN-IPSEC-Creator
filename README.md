# PAN-IPSEC-Creator

Used to create IPSEC VPNs on a Palo Alto Firewall.

PLEASE read through the script to understand what it is doing and read through the README! Some modifications may be needed for your environment. I made a public version to help people with Palo Alto's API as their documentation is lacking. This script is not the "end all, be all". You will need to set it up first.

Edit config.toml with all the settings you require. Some items are left blank as they will be different compared to mine!

Edit endpoints.csv with your VPN settings that are different between VPNs.

You will need to manually run a commit from the GUI or cmd line. This is a safe guard, however, pan-os-python does provide a commit function if you are so inclined.

### Verions

Python - 3.7
PAN-OS - 9.0.9

Tested against python 3.7 and should work for any recent python3. It looks like pan-os-python requires >3.5 so I would stick to those versions of python.

## Description:
Used to add IPSEC VPNs to Palo Alto Firewalls. Support for HA environments has been implemented. Use config.toml for the settings. No commit command is sent the firewall. Commits will need to be ran manually from the GUI to verify the correct config. My environment is fairly static. This means, many of my settings live in the config.toml. Any dynamic settings live in the endpoints.csv for VPN specific settings. Certain settings, like `application` for security rules, may vary based on what you want to allow though a VPN. This setting could be added as column to the endpoints.csv. You will need to modify the script accordingly. 

There are 7 primary steps.

1. Create IKE Gateways
2. Create Tunnel Interfaces
3. Add Tunnel's to a Zone
4. Create IPSEC Tunnels
5. Create Address Objects
6. Create Static Routes
7. Add Firewall Rule to allow traffic.

This script's usages assumes settings for my environment. 

1. You only have 1 router on your PAN.
2. All of your VPNs fall under a single Address Group.
3. You have your firewalls in HA. I'm not sure how it will react to a single PAN. Comment out the HA section if not needed.
4. You must manually commit from the GUI or cmd line. I perform a visual check on my firewall to make sure the script created what it was supposed to.
5. You use Tunnel interfaces for your VPNs. Modifications will be required if you don't used tunnel interfaces.
6. for Peer ID, I used a hostname. If you use and IP, then use the IP in endpoints.csv for the `hostname`.

Be sure to install the requirements using something like `pip3 install -r requirements.txt`.

## Usage
`python PAN-IPSEC-Creator`

## Requirements
* [`pan-os-python`](https://github.com/PaloAltoNetworks/pan-os-python)
* [`toml`](https://github.com/uiri/toml)

## Files
`config.toml` - Holds the static configuration variables. This uses TOML which is like an .ini file. I find that syntax more readable than JSON or YAML.

`endpoints.csv` - holds the dynamic configurations for the VPNs

`create_vpns.py` - production script to run

## Notes for endpoints.csv
1. IKE Gateway name cannot be more than 31 chars
2. IPSEC tunnel name cannot be more than 31 chars
3. tunnel in tunnel.x needs to be lowercase.

