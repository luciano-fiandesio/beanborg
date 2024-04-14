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
    package_data={'': ['classification/prompts/system.txt']},
    include_package_data=True,
    scripts=['bin/bb_import', 'bin/bb_mover', 'bin/bb_archive']
)