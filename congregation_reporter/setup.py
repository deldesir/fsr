from setuptools import setup, find_packages

setup(
    name='congregation-reporter',
    version='0.1.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'click',
        # Add other dependencies here if any are introduced later
    ],
    entry_points={
        'console_scripts': [
            'congoreport=congregation_reporter.cli:cli',
        ],
    },
    author='CLI User',
    author_email='cli.user@example.com',
    description='A CLI tool to process congregation JSON data and generate reports.',
    long_description='A CLI tool to process congregation JSON data and generate reports.',
    # long_description_content_type='text/markdown', # Omit if not using Markdown for long_description
    url='https://github.com/user/congregation-reporter', # Placeholder URL
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License', # Example, choose as appropriate
        'Operating System :: OS Independent',
        'Development Status :: 3 - Alpha',      # Example status
        'Intended Audience :: End Users/Desktop',
        'Topic :: Utilities',
    ],
    python_requires='>=3.8', # Example, specify compatible Python versions
)
