from setuptools import setup, find_packages

setup(
    name='PyTouch',
    version='0.1.0',
    packages=find_packages(),
    url='https://github.com/campact/kb-user',
    license='MIT License',
    author='Moritz Nisblé',
    author_email='moritz.nisble@gmx.de',
    description='Python reimplementation of the foozled typing tutor KTouch from KDEs education package.',
    package_data={
        'pytouch.resources.courses': ['*.xsd', '*.xml'],
    },
    # Also include license and readme in installation
    data_files=[('', ['LICENSE', 'README.md'])],
    # Bootstrap nose to be able to replace setuptools test command by nosetests
    setup_requires=['nose>=1.0'],
    install_requires=[
        'SQLAlchemy',
        'lxml',
    ],
    tests_require=['coverage'],
    entry_points={
        'console_scripts': [
            'pytouch = pytouch.main:manage',
        ],
        'gui_scripts': [
            'pytouch-gui = pytouch.main:manage',
        ]
    }
)
