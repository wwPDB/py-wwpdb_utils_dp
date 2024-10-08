# File: setup.py
# Date: 15-Oct-2018
#
# Update:
#
import re

from setuptools import find_packages
from setuptools import setup

packages = []
thisPackage = "wwpdb.utils.dp"

with open("wwpdb/utils/dp/__init__.py", "r") as fd:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', fd.read(), re.MULTILINE).group(1)

if not version:
    raise RuntimeError("Cannot find version information")

setup(
    name=thisPackage,
    version=version,
    description="API for Common Data Processing Operations",
    long_description="See:  README.md",
    author="John Westbrook",
    author_email="john.westbrook@rcsb.org",
    url="https://github.com/wwpdb/py-wwpdb_utils_dp",
    #
    license="Apache 2.0",
    classifiers=[
        "Development Status :: 3 - Alpha",
        # 'Development Status :: 5 - Production/Stable',
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    entry_points={"console_scripts": []},
    #
    install_requires=[
        "mmcif ~= 0.18",
        "wwpdb.utils.config >= 0.34",
        "wwpdb.io",
        "gemmi >= 0.4",
    ],
    packages=find_packages(exclude=["wwpdb.mock-data", "wwpdb.utils.tests-dp", "tests.*"]),
    package_data={
        # If any package contains *.md or *.rst ...  files, include them:
        "": ["*.md", "*.rst", "*.txt", "*.cfg"],
    },
    #
    # These basic tests require no database services -
    test_suite="wwpdb.utils.tests-dp",
    tests_require=["tox", "wwpdb.utils.testing"],
    #
    # Not configured ...
    extras_require={
        "dev": ["check-manifest"],
        "test": ["coverage"],
    },
    # Added for
    command_options={
        "build_sphinx": {
            "project": ("setup.py", thisPackage),
            "version": ("setup.py", version),
            "release": ("setup.py", version),
        }
    },
    # This setting for namespace package support -
    zip_safe=False,
)
