#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages


with open('README.md') as f:
    long_description = f.read()


requirements = [
    'click',
    'hyper',
    'tornado',
    'requests',
    'python-dateutil'
]

setup_requirements = [
    'wheel'
]

test_requirements = [
    'pytest'
]

setup(
    name='avs',
    version='0.3.0',
    description="Python implementation of Alexa Voice Service App",
    long_description=long_description,
    long_description_content_type='text/markdown',
    author="Yihui Xiong",
    author_email='yihui.xiong@hotmail.com',
    url='https://github.com/respeaker/avs',
    packages=find_packages(include=['avs']),
    include_package_data=True,
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'alexa=avs.main:main',
            'alexa-tap=avs.alexa:main',
            'alexa-auth=avs.auth:main',
            'dueros-auth=avs.auth:main',
            'alexa-audio-check=avs.check:main'
        ],
    },
    license="GNU General Public License v3",
    zip_safe=False,
    keywords='alexa voice service',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements,
    setup_requires=setup_requirements,
)
