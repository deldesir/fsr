from setuptools import setup, find_packages

setup(
    name="fsr",
    version="0.1.0",
    packages=find_packages(include=['cli', 'core', 'reports']),
    install_requires=[
        "click",
    ],
    entry_points={
        "console_scripts": [
            "fsr=cli:cli",
        ],
    },
    author="Blondel"
    author_email="", # Placeholder
    description="A CLI tool to process congregation field service data from a JSON file.",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url="https://github.com/deldesir/fsr",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GPL-3.0",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
