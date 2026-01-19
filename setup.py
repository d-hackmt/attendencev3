# to make our modular logic into package

from setuptools import setup,find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()
    
    
setup(
    name="Attendence",
    version="0.3",
    author="dmt",
    packages=find_packages(),
    install_requires = requirements,
)