from setuptools import setup
from setuptools import find_packages


setup(
    name='cointrol',
    version='0.0.1',
    packages=find_packages(),
    url='https://github.com/jkbrzt/cointrol',
    license='MIT',
    author='Jakub Roztocil',
    author_email='jakub@roztocil.co',
    description='Realtime dashboard and Bitcoin trading bot for Bitstamp',
    entry_points={
        'console_scripts': [
            'cointrol-server = cointrol.server.app:main',
            'cointrol-trader = cointrol.trader.app:main',
        ],
    },
)
