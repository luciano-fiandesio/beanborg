from setuptools import setup, find_packages

# Read requirements.txt
with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='beanborg',
    version='0.1',
    author='Luciano Fiandesio',
    author_email='luciano@fiandes.io',
    url='https://github.com/luciano-fiandesio/beanborg',
    packages=find_packages(),
    install_requires=required,
    include_package_data=True,
    scripts=['bin/bb_import', 'bin/bb_mover', 'bin/bb_archive']
    # entry_points={
    #     'console_scripts': [
    #     	'bb_mover=beanborg:bb_mover.main',
    #     	'bb_archive=beanborg:bb_archive.main',
    #     	'bb_import=beanborg:bb_import.main'
    #     ],
    # }
)