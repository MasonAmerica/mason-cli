from setuptools import setup, find_packages

import os


root = os.path.dirname(os.path.realpath(__file__))

# Read version
with open(os.path.join(root, "VERSION"), "r") as f:
    version = f.read().strip()

# Write version.py
with open(os.path.join(root, "masonlib/version.py"), "w") as f:
    f.write("__version__ = '{}'".format(version))


setup(
    name='mason-cli',
    version=version,
    zip_safe=False,
    packages=find_packages(),
    install_requires=[
        'click==7.0',
        'requests',
        'tqdm',
        'pyyaml',
        'six',
        'colorama',
        'packaging',
        'pyaxmlparser',
        'future'  # Needed for Python 2 compatibility
    ],
    entry_points={
        'console_scripts': [
            'mason = masonlib.mason:cli'
        ]
    },
    include_package_data=True,
)
