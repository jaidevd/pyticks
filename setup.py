from setuptools import setup, find_packages
NAME = "pyticks"

setup(
    name=NAME,
    version='0.0.1',
    author='Jaidev Deshpande',
    author_email='deshpande.jaidev@gmail.com',
    entry_points={
        'console_scripts': ['pyticks = pyticks_cli:main'],
               },
    packages=find_packages(),
)
