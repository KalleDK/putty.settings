import re
import paramiko
import winreg
import pathlib
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa

STORE = winreg.HKEY_CURRENT_USER
PUTTY_PATH = pathlib.PureWindowsPath('Software', 'SimonTatham', 'PuTTY')

class SshHostKeys:

    path = PUTTY_PATH.joinpath('SshHostKeys')
    putty_entry_pattern = re.compile(r'(?P<key_type>.+)@(?P<port>.+):(?P<hostname>.+)')
    paramiko_entry_pattern = re.compile(r'\[(?P<hostname>.+)\]:(?P<port>.+)')

    def __init__(self, host_keys: paramiko.HostKeys = None ):
        self.host_keys = host_keys or paramiko.HostKeys()

    @classmethod
    def get_from_registry(cls):
        with winreg.OpenKey(cls.store, cls.path, 0, winreg.KEY_ALL_ACCESS) as key:
            size = winreg.QueryInfoKey(key)[1]
            return [winreg.EnumValue(key, i)[:2] for i in range(size)]

    @classmethod
    def set_to_registry(cls, entries):
        with winreg.OpenKey(cls.store, cls.path, 0, winreg.KEY_ALL_ACCESS) as key:
            for entry in entries:
                winreg.SetValueEx(key, entry[0], 0, 1, entry[1])

    @classmethod
    def parse_entry(cls, putty_entry):
        putty_host, putty_key = putty_entry
        m = cls.putty_host_pattern.match(putty_host)
        if m:
            if m.group('port') != '22':
                paramiko_hostname = "[{hostname}]:{port}".format(hostname=m.group('hostname'), port=m.group('port'))
            else:
                paramiko_hostname = "{hostname}".format(hostname=m.group('hostname'))

            if m.group('key_type') == 'rsa2':
                paramiko_key = cls.to_ssh_rsa(putty_key)
                paramiko_key_type = 'ssh-rsa'
            else:
                raise Exception("Can't handle this key")
        else:
            raise Exception("Can't handle this key")
        return paramiko_hostname, paramiko_key_type, paramiko_key

    @staticmethod
    def to_ssh_rsa(putty_data):
        e, n = (int(x, 0) for x in putty_data.split(','))
        return paramiko.RSAKey(key=rsa.RSAPublicNumbers(e=e, n=n).public_key(default_backend()))

    @staticmethod
    def from_ssh_rsa(key):
        return 0

    def load(self):
        # Getting entries from the registry
        putty_entries = self.get_from_registry()

        # Convert the keys
        for putty_entry in putty_entries:
            self.host_keys.add(*self.parse_entry(putty_entry))

    def save(self):

        putty_entries = []

        # Convert the keys
        for host_key in self.host_keys._entries:
            hostentries = [host_key.hostnames] if isinstance(host_key.hostnames, str) else host_key.hostnames

            for hostentry in hostentries:
                m = self.paramiko_host_pattern.match(hostentry)
                if m:
                    hostname = m.group('hostname')
                    port = m.group('port')
                else:
                    hostname = hostentry
                    port = '22'

                if host_key.key.get_name() == 'ssh-rsa':
                    putty_key_type = 'rsa2'
                    putty_key = '{e},{n}'.format(e=hex(host_key.key.public_numbers.e), n=hex(host_key.key.public_numbers.n))

                putty_hostname = '{key_type}@{port}:{hostname}'.format(key_type=putty_key_type, port=port, hostname=hostname)

                putty_entries.append((putty_hostname, putty_key))

        # Save the keys
        self.set_to_registry(putty_entries)