# setup.py

from setuptools import setup, find_packages

setup(
    name='ZugaCloud',
    version='1.1.0',
    description='Infinite Video Storage Software with AWS S3 Integration',
    author='Your Name',
    author_email='your.email@example.com',
    packages=find_packages(),
    install_requires=[
        'boto3',
        'Pillow',
        'opencv-python',
        'watchdog',
    ],
    entry_points={
        'console_scripts': [
            'zugacloud=main:main',
        ],
    },
    include_package_data=True,
    package_data={
        'frontend': [
            'themes/*.tcl',
            'assets/icons/*',
            'assets/thumbnails/*',
            'assets/zugacloud_logo.png'
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
)
