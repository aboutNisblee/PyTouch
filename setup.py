from setuptools import setup, find_packages

setup(
    name='PyTouch',
    version='0.1.0',
    packages=find_packages(exclude=['tests', 'tools']),
    url='https://github.com/campact/kb-user',
    license='MIT License',
    author='Moritz Nisblé',
    author_email='moritz.nisble@gmx.de',
    description='',
    # Bootstrap nose to be able to replace setuptools test command by nosetests
    setup_requires=['nose>=1.0'],
    install_requires=['SQLAlchemy'],
    tests_require=['coverage'],
)
