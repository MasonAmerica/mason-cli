from setuptools import setup
import os

version_file = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'VERSION'))

setup(
    name='mason-cli',
    version=version_file.read().strip(),
    py_modules=['mason', 'masonlib.mason', 'masonlib.persist', 'masonlib.store', 'masonlib.utils', 
		'lib.apk_parse', 'lib.apk_parse.apk', 'lib.apk_parse.bytecode', 'lib.apk_parse.androconf', 
		'lib.apk_parse.dvm_permissions', 'lib.apk_parse.util'],
    include_package_data=True,
    install_requires=[
        'click',
        'requests',
        'progressbar',
        'pyyaml'
    ],
    entry_points='''
        [console_scripts]
        mason=mason:cli
    ''',
)
