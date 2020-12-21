########################################################################################################################
#
#  create_vpns.py
#
#       Created by: Will Lehnertz
#       Created: 11/25/2020
#       Modified: 11/25/2020
#
#  Description: Used to add IPSEC VPNs to Palo Alto Firewalls. Support for HA environments has been implemented.
#               Use config.toml for the settings. No commit command is sent the firewall. Commits will need to be
#               ran manually from the GUI to verify the correct config.
#
########################################################################################################################

from panos import firewall, objects, network, policies

import toml
import csv

# load settings
settings = toml.load('config.toml')

# connect to firewalls
print("Connecting to Firewalls")
fw = firewall.Firewall(settings['firewalls']['fw'], api_key=settings['api_key']['key'])
fw.set_ha_peers(firewall.Firewall(settings['firewalls']['fw_ha'], api_key=settings['api_key']['key']))

# Check HA pair first #########################
print("Checking HA configuration")
fw.refresh_ha_active()
if not fw.config_synced():
    print("I need to sync the configs first.")
    fw.synchronize_config()
###############################################

# Open endpoints csv
cradle_reader = csv.DictReader(open('endpoints.csv', 'rt', encoding='utf8'))

#######################################################################################################################

# init variables
ike_gateway_arr = []
tunnel_interfaces_arr = []
zone_array = []
ipsec_tunnels_arr = []
address_objs_arr = []
vr = network.VirtualRouter(settings['router_name']['name'])
static_route_arr = []
firewall_rule_arr = []

# iterate over CSV
for row in cradle_reader:
    # ike gateway
    ike_gateway_arr.append(
        network.IkeGateway(name=row['ike_gateway_name'], 
                           version=settings['ike_gateway']['version'], 
                           peer_ip_type=settings['ike_gateway']['peer_ip_type'], 
                           interface=settings['ike_gateway']['interface'], 
                           local_ip_address_type=settings['ike_gateway']['local_ip_address_type'], 
                           local_ip_address=settings['ike_gateway']['local_ip_address'],
                           pre_shared_key=settings['ike_gateway']['pre_shared_key'], 
                           peer_id_type=settings['ike_gateway']['peer_id_type'], 
                           peer_id_value=row['hostname'], 
                           enable_passive_mode=settings['ike_gateway']['enable_passive_mode'], 
                           enable_nat_traversal=settings['ike_gateway']['enable_nat_traversal'],
                           enable_fragmentation=settings['ike_gateway']['enable_fragmentation'], 
                           ikev1_exchange_mode=settings['ike_gateway']['ikev1_exchange_mode'],
                           ikev1_crypto_profile=settings['ike_gateway']['ikev1_crypto_profile'], 
                           enable_dead_peer_detection=settings['ike_gateway']['enable_dead_peer_detection'],
                           ikev2_crypto_profile=settings['ike_gateway']['ikev2_crypto_profile'])
    )

    print("1. Created ike gateway for {}".format(row['hostname']))

    ####################################################################################################################

    # Tunnel interface
    tunnel_interfaces_arr.append(
        network.TunnelInterface(row['tunnel_name'],
                                ip="{}/30".format(row['pan_tunnel']),
                                comment="Tunnel to {}".format(row['hostname']))
    )

    print("2. Created Tunnel Interface for {}".format(row['hostname']))

    ####################################################################################################################

    # Zone
    zone_array.append(row['tunnel_name'])

    print("3. added Zone for {}".format(row['hostname']))

    ####################################################################################################################

    # ipsec Tunnels
    ipsec_tunnels_arr.append(
        network.IpsecTunnel(name=row['ipsec_tunnel_name'], 
                            tunnel_interface=row['tunnel_name'],
                            type=settings['ipsec_tunnel']['type'], 
                            ak_ike_gateway=row['ike_gateway_name'],
                            ak_ipsec_crypto_profile=settings['ipsec_tunnel']['ak_ipsec_crypto_profile'],
                            enable_tunnel_monitor=settings['ipsec_tunnel']['enable_tunnel_monitor'])
    )

    print("4. Created IPSEC Tunnel for {}".format(row['hostname']))

    ####################################################################################################################

    # Network Objects
    address_objs_arr.append(
        objects.AddressObject(name=row['object_name'], 
                              value=row['subnet'], 
                              type=settings['address_object']['type'],
                              description=row['object_description'])
    )

    print("5. added network object for {}".format(row['hostname']))

    ####################################################################################################################

    # Static Routes

    # Pull the Default_vRouter config from the router. This returns a list...
    # This will need to be modified if you have more than one router.
    vr = vr.refreshall(fw)
    vr = vr[0]
    static_route_arr.append(
        network.StaticRoute(name=row['object_name'], 
                            destination=row['object_name'],
                            nexthop_type=settings['static_route']['nexthop_type'], 
                            nexthop=row['local_tunnel'], 
                            interface=row['tunnel_name'],
                            metric=settings['static_route']['metric'])
    )

    print("6. Created static route for {}".format(row['hostname']))

    ####################################################################################################################

    # Firewall Rule

    firewall_rule_arr.append(
        policies.SecurityRule(name=row['firewall_rule_name'], 
                              fromzone=settings['security_rule']['fromzone'],
                              tozone=settings['security_rule']['tozone'], 
                              source=settings['security_rule']['source'], 
                              source_user=settings['security_rule']['source_user'], 
                              hip_profiles=settings['security_rule']['hip_profiles'],
                              destination=row['object_name'], 
                              application=settings['security_rule']['application'],
                              service=settings['security_rule']['service'], 
                              category=settings['security_rule']['category'], 
                              action=settings['security_rule']['action'],
                              log_setting=settings['security_rule']['log_setting'], 
                              virus=settings['security_rule']['virus'], 
                              spyware=settings['security_rule']['spyware'],
                              vulnerability=settings['security_rule']['vulnerability'], 
                              wildfire_analysis=settings['security_rule']['wildfire_analysis'])
    )

    print("7. Created Firewall Rule for {}".format(row['hostname']))

########################################################################################################################
#                                            Send stuff to the firewall                                                #
########################################################################################################################

# Add IKE gateway to FW ###############################################################
fw.extend(ike_gateway_arr)
ike_gateway_arr[0].create_similar()

print("8. Saved ike gateways")

# Add Tunnel Interfaces to FW #########################################################
fw.extend(tunnel_interfaces_arr)
tunnel_interfaces_arr[0].create_similar()

print("9. Saved tunnel interfaces")

# Add Tunnels to zones ################################################################
# Interface to Default_Router

vr = vr.refreshall(fw)
vr = vr[0]
for interface in zone_array:
    vr.interface.append(interface)
fw.add(vr)
vr.create()

print("10. Saved tunnel to VR")

# Add Tunnels to zones ################################################################
zone_obj = network.Zone(name=settings['zone']['name'], mode=settings['zone']['mode'], interface=zone_array)

fw.add(zone_obj)
zone_obj.create()

print("11. Saved zones")

# Add IPSEC Tunnel to FW ##############################################################
fw.extend(ipsec_tunnels_arr)
ipsec_tunnels_arr[0].create_similar()

print("12. Saved IPSEC tunnels")

# Add Addresses and Address groups ####################################################
fw.extend(address_objs_arr)
# this is bulk upload to PAN
address_objs_arr[0].create_similar()

print("13. Saved Address objects")

# get the groups
address_group = objects.AddressGroup(name=settings['address_group']['name'])
address_group = address_group.refreshall(fw)

for group in address_group:
    if group.name == settings['address_group']['name']:
        print("12.1. adding address to group")
        # will need for loop to bulk add Addresses
        for address in address_objs_arr:
            group.static_value.append(address.name)
        fw.add(group)
        group.create()

print("14. Saved Address groups")

# add the static router to the VirtualRouter #########################################

# This is how it should work, but an exception is thrown saying
# static-route is already in use for some reason.
#
# vr.extend(static_route_arr)
# static_route_arr[0].create_similar()

# So instead, this is used.
for route in static_route_arr:
    vr.add(route)
    route.create()

print("15. Saved Static routes")

# Add Firewall Rule to FW ############################################################
rb = policies.Rulebase()
fw.add(rb)
rb.extend(firewall_rule_arr)
firewall_rule_arr[0].create_similar()

print("16. Saved Firewall rules")
print("Yay! Script is done! Now commit your changes on the firewall.")

