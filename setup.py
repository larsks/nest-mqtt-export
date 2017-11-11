from setuptools import setup, find_packages

setup(
    name='nestmqtt',
    version='0.1',
    author='Lars Kellogg-Stedman',
    author_email='lars@oddbit.com',
    url='https://github.com/larsks/nestmqtt',
    packages=find_packages(),
    install_requires=[
        'python-nest',
        'paho_mqtt',
    ],
    entry_points={
        'console_scripts': [
            'nest-export-mqtt = nestmqtt.main:main',
        ],
    }
)
