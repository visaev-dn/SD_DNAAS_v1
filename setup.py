#!/usr/bin/env python3
"""
Setup script for Network LAB Automation Framework
"""

from setuptools import setup, find_packages

setup(
    name="network-lab-automation",
    version="1.0.0",
    description="Network LAB Automation Framework for spine-leaf topologies",
    author="Network Automation Team",
    packages=find_packages(),
    install_requires=[
        "paramiko>=2.8.1",
        "jinja2>=3.0.0",
        "pyyaml>=6.0",
        "netmiko>=4.1.0",
        "ncclient>=0.6.0",
        "requests>=2.28.0",
    ],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "lab-automation=main:main",
        ],
    },
) 