from setuptools import setup, find_packages

setup(
    name="pygit",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "click>=8.0.0",
        "rich>=10.0.0",
        "cryptography>=36.0.0",
    ],
    entry_points={
        "console_scripts": [
            "pygit=pygit.cli:main",
        ],
    },
    python_requires=">=3.10",
    author="Your Name",
    author_email="your.email@example.com",
    description="A Git-like version control system implemented in Python",
    keywords="git, version control, vcs",
    url="https://github.com/yourusername/pygit",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
    ],
)
