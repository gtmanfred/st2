# -*- coding: utf-8 -*-
try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

setup(
    name='st2stactioncontroller',
    version='0.1.0',
    description='',
    author='StackStorm',
    author_email='info@stackstorm.com',
    install_requires=[
        "pecan",
    ],
    test_suite='st2stactioncontroller',
    zip_safe=False,
    include_package_data=True,
    packages=find_packages(exclude=['ez_setup'])
)