"""
setup.py - package configuration for ErFlasher MDM Tools
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="erflasher-mdm-tools",
    version="2.0.0",
    description="ErFlasher MDM Tools — cross-platform MDM patcher for iOS devices (Windows & Linux)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Erzambayu",
    url="https://github.com/Erzambayu/MDMPatcher-Enhanced",
    
    packages=find_packages(),
    package_data={
        "src.resources": ["*.pdf", "*.dylib"],
    },
    
    install_requires=[
        "customtkinter>=5.2.0",
        "Pillow>=10.0.0",
        "pycryptodome>=3.19.0",
        "pyusb>=1.2.1",
    ],
    
    extras_require={
        "pymd3": ["pymobiledevice3>=4.0.0"],
        "dev": ["pyinstaller>=6.0.0", "black", "isort"],
    },
    
    entry_points={
        "console_scripts": [
            "erflasher=main:main",
        ],
    },
    
    python_requires=">=3.10",
    
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Utilities",
    ],
)
