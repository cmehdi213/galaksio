#!/usr/bin/env python3
"""
Galaksio 2 - Modern Galaxy Workflow Interface
A modern, responsive web interface for running Galaxy workflows with enhanced user experience and accessibility.
"""

from setuptools import setup, find_packages
import os

# Read the requirements.txt file
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    with open(requirements_path, 'r') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return requirements

# Read the README file for long description
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "Galaksio 2 - Modern Galaxy Workflow Interface"

# Read version from VERSION file
def read_version():
    version_path = os.path.join(os.path.dirname(__file__), 'VERSION')
    if os.path.exists(version_path):
        with open(version_path, 'r') as f:
            for line in f:
                if 'Galaksio v' in line:
                    return line.split('v')[1].split(' ')[0]
    return "0.4.0"

setup(
    name="galaksio",
    version=read_version(),
    author="Original: SGBC, Updated: cmehdi213",
    author_email="cmehdi213@example.com",
    description="A modern, responsive web interface for running Galaxy workflows",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/cmehdi213/galaksio",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
    python_requires=">=3.9",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
        ],
        "docker": [
            "docker>=6.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "galaksio=server.launch_server:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.html", "*.css", "*.js", "*.json", "*.png", "*.ico", "*.txt", "*.cfg"],
    },
    zip_safe=False,
    keywords="galaxy bioinformatics workflows web-interface",
    project_urls={
        "Bug Reports": "https://github.com/cmehdi213/galaksio/issues",
        "Source": "https://github.com/cmehdi213/galaksio",
        "Documentation": "https://galaksio.readthedocs.io/",
    },
)
