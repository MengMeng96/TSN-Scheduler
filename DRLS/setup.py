from __future__ import print_function
from setuptools import setup, find_packages
import sys

setup(
    name="packer",
    version="0.1.0",
    author="",  #作者名字
    author_email="",
    description="Python Framework.",
    license="MIT",
    url="",  #github地址或其他地址
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Environment :: Web Environment",
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: Chinese',
        'Operating System :: MacOS',
        'Operating System :: Microsoft',
        'Operating System :: POSIX',
        'Operating System :: Unix',
        'Topic :: NLP',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    install_requires=[
            # 'numpy>=1.14.0'   #所需要包的版本号
    ],
    zip_safe=True,
)