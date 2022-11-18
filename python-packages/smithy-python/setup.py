#!/usr/bin/env python
import codecs
import os.path
import re

from setuptools import find_packages, setup

here = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    return codecs.open(os.path.join(here, *parts), "r", encoding="utf-8").read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


requires = ["awscrt>=0.15,<1.0"]

setup(
    name="smithy-python",
    version=find_version("smithy_python", "__init__.py"),
    description="Core libraries for Smithy defined services in Python",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Amazon Web Services",
    keywords="python sdk amazon smithy codegen",
    url="https://github.com/awslabs/smithy-python",
    scripts=[],
    packages=find_packages(exclude=["tests*", "codegen", "designs"]),
    include_package_data=True,
    install_requires=requires,
    extras_require={},
    python_requires=">=3.11",
    project_urls={
        "Source": "https://github.com/awslabs/smithy-python",
        "Changelog": "https://github.com/awslabs/smithy-python/blob/develop/CHANGES.md",
    },
    license="Apache License 2.0",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Natural Language :: English",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Software Development :: Libraries",
    ],
)
