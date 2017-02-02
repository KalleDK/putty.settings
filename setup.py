from setuptools import setup, find_packages
import pathlib


def read(*names):
    return open(pathlib.Path(pathlib.Path(__file__).parent, *names)).read()

install_requires = [
    'paramiko'
]

setup(
    name='putty.settings',
    version='1.0.0',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages=['putty'],
    url='https://github.com/KalleDK/putty.settings.git',
    license='MIT',
    author='Kalle R. Møller',
    author_email='python@k-moeller.dk',
    description='Bindings for Putty\'s settings',
    install_requires=install_requires,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
        'Operating System :: Microsoft',
    ],
    keywords='putty paramiko development',
)
