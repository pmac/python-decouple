
from setuptools import setup, find_packages

setup(
    name=itauapipix',
    version='0.4',
    packages=find_packages(),
    #package_data={'itauapipix': ['server_certs/*.cer']},
    install_requires=[
        'pyOpenSSL >= 24.2.1',
        'requests == 2.31.0',
    ],
)
