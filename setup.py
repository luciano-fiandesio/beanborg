from setuptools import setup, find_packages

setup(
    name='beanborg',
    version='0.1',
    author='Luciano Fiandesio',
    author_email='luciano@fiandes.io',
    url='https://github.com/luciano-fiandesio/beanborg',
    packages=find_packages(),
    install_requires=[
       "beancount==2.3.3",
       "pyyaml==6.0.1",
       "rich==13.6.0",
       "prompt-toolkit==3.0.39",
    ],
    entry_points={
        'console_scripts': [
        	'bb_mover=beanborg:bb_mover.main',
        	'bb_archive=beanborg:bb_archive.main',
        	'bb_import=beanborg:bb_import.main'
        ],
    }
)
