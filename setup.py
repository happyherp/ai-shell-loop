from setuptools import setup, find_packages

setup(
    name="ai-do",
    version="0.1.0",
    description="A tool to run shell commands iteratively using AI",
    author="Carlos Freund",
    author_email="carlosfreund@gmail.com",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'ai-do=aishell:main',  # Define the CLI command and the entry point
        ],
    },
    install_requires=[
        'openai==1.45.0',
        'pydantic==2.9.1',
        'PyYAML==6.0.2'
    ],
    python_requires='>=3.6',
)
