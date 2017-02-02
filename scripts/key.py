#!/usr/bin/env python3
import paramiko
from putty.settings import SshHostKeys

ssh_host_keys = SshHostKeys()
paramiko_host_keys = paramiko.HostKeys()

ssh_host_keys.load()
ssh_host_keys.add_to_paramiko_host_keys(paramiko_host_keys)

print(ssh_host_keys.host_keys.pop('rsa2@22:diablo2.dk', None))

ssh_host_keys.save()

# Would love an easier way to iterate
#for hostname in paramiko_host_keys.keys():
#    for key, val in paramiko_host_keys.lookup(hostname).items():
#        print(hostname + " " + str(key.__str__()) + " " + str(val.get_base64()))



