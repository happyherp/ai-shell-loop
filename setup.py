from setuptools import setup, find_packages

setup(
    name="ai-shell-loop",
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    description="A command line tool that lets an AI do work for you.",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    author="Carlos Freund",
    author_email="carlosfreund@gmail.com",
    license="Apache License 2.0",
    url="https://github.com/happyherp/ai-shell-loop",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'ai-do=ai_shell.aishell:main',
        ],
    },
    install_requires=[
        'openai>=0.28.0,<2.0.0',  # Support both older 0.x and newer 1.x versions
        'pydantic==2.9.1',
        'PyYAML==6.0.2',
        'appdirs==1.4.4'
    ],
    python_requires='>=3.6',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX :: Linux",   # For Linux systems
        "Operating System :: MacOS :: MacOS X", # For macOS
    ],
)
