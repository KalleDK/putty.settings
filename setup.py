from setuptools import setup, find_packages
import pathlib


def read(*names):
    return open(pathlib.Path(pathlib.Path(__file__).parent, *names)).read()

install_requires = [
    'setuptools>=34.0.0',
    'pip>=9.0.0',
    'paramiko'
]

setup(
    name='putty.settings',
    version='1.0.0',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages=['putty'],
    url='https://github.com/KalleDK/putty.settings.git',
    license='',
    author='km',
    author_email='python@k-moeller.dk',
    description='Putty to known_hosts',
    install_requires=install_requires
)
