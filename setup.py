from setuptools import setup

setup(
    name='mason-cli',
    version='0.1',
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
