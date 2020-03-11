import os

from setuptools import find_packages
from setuptools import setup

root = os.path.dirname(os.path.realpath(__file__))

# Read version
with open(os.path.join(root, "VERSION")) as f:
    version = f.read().strip()

# Write version.py
with open(os.path.join(root, "cli/version.py"), "w") as f:
    f.write("__version__ = '{}'\n".format(version))

setup(
    name='mason-cli',
    version=version,
    zip_safe=False,
    packages=find_packages(),
    install_requires=[
        'click>=7.0',
        'click-log',
        'pick',
        'requests',
        'requests-toolbelt',
        'tqdm',
        'pyyaml',
        'six',
        'packaging',
        'pyaxmlparser>=0.3.22',
        'adb_shell>=0.1.2',
        'twisted>=19.10.0',
        'autobahn>=19.11.1',
        'service_identity',
        'pyopenssl>=19.1.0',
        'pyasn1>=0.4.7',
        'tonyg-rfc3339'
    ],
    entry_points={
        'console_scripts': [
            'mason = cli.mason:main'
        ]
    },
    include_package_data=True,
    test_suite="tests",
)
