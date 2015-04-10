from setuptools import setup, find_packages
import keyring

msg = """PyTicks requires your GitHub credentials to automatically create issues.
PyTicks uses keyring for storing your password, which will be stored under a
service called "pyticks".
Note that this is a one time request.
"""
print msg
username = raw_input("GitHub username: ")
password = raw_input("GitHub password: ")
keyring.set_password("pyticks", username, password)

NAME = "pyticks"

setup(
    name=NAME,
    version='0.0.1',
    author='Jaidev Deshpande',
    author_email='deshpande.jaidev@gmail.com',
    entry_points={
        'console_scripts': ['pyticks = cli:main'],
               },
    packages=find_packages(),
)
