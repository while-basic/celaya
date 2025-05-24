# ----------------------------------------------------------------------------
#  File:        setup.py
#  Project:     Celaya Solutions
#  Created by:  Celaya Solutions, 2025
#  Author:      Christopher Celaya <chris@celayasolutions.com>
#  Description: Setup script for Celaya Python packages
#  Version:     1.0.0
#  License:     BSL (SPDX id BUSL)
#  Last Update: (May 2025)
# ----------------------------------------------------------------------------

"""
Setup script for Celaya Python packages.

Installs the celaya_python and lyra_os packages.
"""

from setuptools import setup, find_packages

setup(
    name="celaya-consensus",
    version="1.0.0",
    description="Multi-agent consensus framework for Celaya",
    author="Celaya Solutions",
    author_email="chris@celayasolutions.com",
    url="https://github.com/celaya/celaya",
    packages=find_packages(include=["celaya_python", "celaya_python.*", "lyra_os", "lyra_os.*"]),
    install_requires=[
        "pyyaml>=6.0",
        "rich>=12.0.0",
        "cryptography>=39.0.0",
        "asyncio>=3.4.3",
    ],
    entry_points={
        "console_scripts": [
            "lyra=lyra_os.bin.lyra:main",
            "celaya_python=celaya_python.cli.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: Other/Proprietary License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
) 