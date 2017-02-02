import re
import paramiko
import winreg
import pathlib
import typing
import logging
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa

logger = logging.getLevelName(__name__)

STORE = winreg.HKEY_CURRENT_USER
PUTTY_PATH = pathlib.PureWindowsPath('Software', 'SimonTatham', 'PuTTY')


paramiko_to_putty_key = {
    "ssh-rsa": "rsa2"
}

putty_to_paramiko_key = {val: key for key, val in paramiko_to_putty_key.items()}


class HostKeyEntry:

    putty_host_entry_pattern = re.compile(r'(?P<key_type>.+)@(?P<port>.+):(?P<hostname>.+)')
    paramiko_host_entry_pattern = re.compile(r'\[(?P<hostname>.+)\]:(?P<port>.+)')

    def __init__(self, hostname: str = None, port: str = None, key_type: str = None, key: paramiko.PKey = None):
        self.hostname = hostname
        self.port = port
        self.key_type = key_type
        self.key = key

    @property
    def paramiko_host_entry(self):
        if self.port == '22':
            return self.hostname
        else:
            return "[{hostname}]:{port}".format(hostname=self.hostname, port=self.port)

    @paramiko_host_entry.setter
    def paramiko_host_entry(self, value):
        m = self.paramiko_host_entry_pattern.match(value)
        if m:
            self.hostname = m.group('hostname')
            self.port = m.group('port')
        else:
            self.hostname = value
            self.port = '22'

    @property
    def paramiko_key_type(self):
        return self.key_type

    @paramiko_key_type.setter
    def paramiko_key_type(self, value):
        self.key_type = value

    @property
    def paramiko_key(self):
        return self.key

    @paramiko_key.setter
    def paramiko_key(self, value):
        self.key = value

    @property
    def putty_key_type(self):
        return paramiko_to_putty_key[self.key_type]

    @putty_key_type.setter
    def putty_key_type(self, value):
        self.key_type = putty_to_paramiko_key[value]

    @property
    def putty_host_entry(self):
        return "{key_type}@{port}:{hostname}".format(key_type=self.putty_key_type, port=self.port, hostname=self.hostname)

    @putty_host_entry.setter
    def putty_host_entry(self, value):
        m = self.putty_host_entry_pattern.match(value)
        if m:
            self.hostname = m.group('hostname')
            self.port = m.group('port')
            self.putty_key_type = m.group('key_type')
        else:
            raise Exception("Not valid host_entry")

    @property
    def putty_key(self):
        if self.key_type == 'ssh-rsa' and isinstance(self.key, paramiko.RSAKey):
            return '{e},{n}'.format(e=hex(self.key.public_numbers.e), n=hex(self.key.public_numbers.n))

    @putty_key.setter
    def putty_key(self, value):
        if self.key_type == 'ssh-rsa':
            e, n = (int(x, 0) for x in value.split(','))
            self.key = paramiko.RSAKey(key=rsa.RSAPublicNumbers(e=e, n=n).public_key(default_backend()))

    @classmethod
    def from_registry_entry(cls, entry: typing.Tuple[str, str, int]):
        o = cls()
        o.putty_host_entry = entry[0]
        o.putty_key = entry[1]
        return o

    @classmethod
    def from_paramiko_entry(cls, host_entry, key_type, key):
        o = cls()
        o.paramiko_host_entry = host_entry
        o.paramiko_key_type = key_type
        o.paramiko_key = key
        return o


class SshHostKeys:

    path = str(PUTTY_PATH.joinpath('SshHostKeys'))

    def __init__(self):
        self.host_keys: typing.Dict[str, HostKeyEntry] = {}

    def load(self):
        for registry_entry in self.get_from_registry():
            try:
                self.add(HostKeyEntry.from_registry_entry(registry_entry))
            except Exception:
                logger.info("Invalid keyformat {}".format(registry_entry))

    def save(self):
        entries_to_remove = []
        for registry_entry in self.get_from_registry():
            if self.host_keys.get(registry_entry[0]) is None:
                entries_to_remove.append(registry_entry[0])
        self.delete_from_registry(entries_to_remove)

        self.set_registry_to(self.host_keys)

    def add(self, host_key_entry: HostKeyEntry):
        self.host_keys[host_key_entry.putty_host_entry] = host_key_entry

    def add_from_paramiko_host_keys(self, host_keys: paramiko.HostKeys):
        for host_entry in host_keys.keys():
            for key_type, key in host_keys.lookup(host_entry).items():
                self.add(HostKeyEntry.from_paramiko_entry(host_entry=host_entry, key_type=key_type, key=key))

    def add_to_paramiko_host_keys(self, host_keys: paramiko.HostKeys):
        for key_type, host_key in self.host_keys.items():
            host_keys.add(hostname=host_key.paramiko_host_entry, keytype=host_key.paramiko_key_type, key=host_key.paramiko_key)

    @classmethod
    def delete_from_registry(cls, entries):
        with winreg.OpenKey(STORE, cls.path, 0, winreg.KEY_ALL_ACCESS) as key:
            for entry in entries:
                winreg.DeleteValue(key, entry)

    @classmethod
    def get_from_registry(cls):
        with winreg.OpenKey(STORE, cls.path, 0, winreg.KEY_ALL_ACCESS) as key:
            size = winreg.QueryInfoKey(key)[1]
            return [winreg.EnumValue(key, i) for i in range(size)]

    @classmethod
    def set_registry_to(cls, host_keys):
        with winreg.OpenKey(STORE, cls.path, 0, winreg.KEY_ALL_ACCESS) as key:
            for key_type, host_key in host_keys.items():
                try:
                    winreg.SetValueEx(key, host_key.putty_host_entry, 0, 1, host_key.putty_key)
                except Exception:
                    logger.info("Invalid keyformat {}".format(host_key))
