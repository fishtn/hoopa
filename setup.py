#!/usr/bin/env python
import os
import re
import sys

from setuptools import find_packages, setup


_version_re = re.compile(r"__version__\s+=\s+(.*)")

PY_VER = sys.version_info

if PY_VER < (3, 7):
    raise RuntimeError("hoopa doesn't support Python version prior 3.7")


def read_version():
    regexp = re.compile(r'^__version__\W*=\W*"([\d.abrc]+)"')
    init_py = os.path.join(os.path.dirname(__file__), "hoopa", "__init__.py")
    with open(init_py) as f:
        for line in f:
            match = regexp.match(line)
            if match is not None:
                return match.group(1)


def read(file_name):
    with open(
        os.path.join(os.path.dirname(__file__), file_name), mode="r", encoding="utf-8"
    ) as f:
        return f.read()


requires = [
    "aiohttp>=3.9.5",
    "httpx[http2]>=0.17.0",
    "redis>=4.6.0",
    "requests",
    "parsel",
    "aiodns",
    "charset-normalizer",
    "arrow",
    "w3lib",
    "loguru",
    "ujson",
    "lxml",
]


setup(
    name="hoopa",
    version=read_version(),
    author="fishtn",
    description="Asynchronous crawler micro-framework based on python.",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    author_email="",
    python_requires=">=3.9",
    install_requires=requires,
    url="https://github.com/fishtn/hoopa",
    packages=find_packages(),
    license="MIT",
    classifiers=[
        "Framework :: AsyncIO",
        "Intended Audience :: Developers",
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX :: BSD",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3.9",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    extras_require={"uvloop": ["uvloop"]},
    entry_points={"console_scripts": ["hoopa = hoopa.commands.cmdline:execute"]},
    include_package_data=True
)
