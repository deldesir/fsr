from setuptools import setup, find_packages

setup(
    name='fsr',
    version='0.1.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'click',
        # Add other dependencies here if any are introduced later
    ],
    entry_points={
        'console_scripts': [
            'fsr=congregation_reporter.cli:cli',
        ],
    },
    author='CLI User',
    author_email='cli.user@example.com',
    description='fsr: Field Service Reporter - A CLI tool to process JSON data and generate activity reports.',
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/user/fsr', # Placeholder URL updated
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
