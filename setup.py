from setuptools import setup, find_packages

def read_requirements():
    with open('requirements.txt', 'r') as req_file:
        return req_file.read().splitlines()

setup(
    name="ampere_core",
    version="1.0",
    packages=find_packages(exclude=["tests*"]),
    package_dir={"": "src"},
    install_requires=read_requirements(),
)
