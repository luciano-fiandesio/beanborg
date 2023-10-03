from setuptools import setup, find_packages

# Read requirements.txt
with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='beanborg',
    version='0.1',
    packages=find_packages(),
    install_requires=required,
    entry_points={
        'console_scripts': [
        	'bb_mover=beanborg:bb_mover.main',
        	'bb_archive=beanborg:bb_archive.main',
        	'bb_import=beanborg:bb_import.main'
        ],
    }
)