from setuptools import setup, find_packages

with open("README.md", "r", encoding='UTF-8') as fh:
    long_description = fh.read()

setup(
    name="tsinghua_net",
    version="1.0.0",
    description="Tsinghua network tools",
    long_description=long_description,
    license="Apache 2.0 Licence",

    url="",
    author="dongbaishun",
    author_email="zcm18@mails.tsinghua.edu.cn",

    packages=find_packages(),
    include_package_data=True,
    platforms="any",
    install_requires=[],

    scripts=[],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache 2.0 License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        'console_scripts': [
            'DRLS=DRLS.__main__:main'
        ]
    }
)

