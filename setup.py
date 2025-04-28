from setuptools import setup, find_packages

setup(
    name="autograding_python_setup",
    version="0.1.0",
    description="A central setup module for shared logic.",
    author="Sean",
    author_email="sean",
    url="https://github.com/Ensign-College/autograding_python_setup",
    packages=find_packages(),
    install_requires=[
        "requests",  # Add any dependencies here
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)