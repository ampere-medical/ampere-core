from setuptools import setup, find_packages

def read_requirements():
    with open('requirements.txt', 'r') as req_file:
        return req_file.read().splitlines()

setup(
    name="APP_NAME",
    version="1.0",
    packages=find_packages(exclude=["tests*", "test*"]),
    package_dir={"": "src"},
    install_requires=read_requirements(),
)

