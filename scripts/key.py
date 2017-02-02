#!/usr/bin/env python3
from putty.settings import PuttyKeys

p = PuttyKeys()

p.load()

# Would love an easier way to iterate
for hostname in p.host_keys.keys():
    for key, val in p.host_keys.lookup(hostname).items():
        print(hostname + " " + str(key.__str__()) + " " + str(val.get_base64()))

#p.save()

