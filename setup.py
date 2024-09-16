from setuptools import setup, find_packages

setup(
    name="ai-do",
    version="0.1.0",
    description="A command line tool that lets an AI do work for you.",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    author="Carlos Freund",
    author_email="carlosfreund@gmail.com",
    license="Apache License 2.0",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'ai-do=ai_shell.aishell:main',  # Define the CLI command and the entry point
        ],
    },
    install_requires=[
        'openai==1.45.0',
        'pydantic==2.9.1',
        'PyYAML==6.0.2'
    ],
    python_requires='>=3.6',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX :: Linux",   # For Linux systems
        "Operating System :: MacOS :: MacOS X", # For macOS
    ],
)
