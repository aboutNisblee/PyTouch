from setuptools import setup, find_packages

setup(
    name='PyTouch',
    version='0.1.0',
    packages=find_packages(exclude=['tests', 'tools']),
    # package_dir={'': 'pytouch'},
    # scripts=['pytouch/main.py'],
    url='https://github.com/campact/kb-user',
    license='MIT License',
    author='Moritz Nisblé',
    author_email='moritz.nisble@gmx.de',
    description='',
    package_data={
        'pytouch.resources.courses': ['*.xsd', '*.xml'],
    },
    # Bootstrap nose to be able to replace setuptools test command by nosetests
    setup_requires=['nose>=1.0'],
    install_requires=[
        'SQLAlchemy',
        'lxml'
    ],
    tests_require=['coverage'],
    entry_points={
        'console_scripts': [
            'pytouch = pytouch.main:run',
        ],
        'gui_scripts': [
            'pytouch-gui = pytouch.main:run',
        ]
    }
)
