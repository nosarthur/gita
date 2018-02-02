from setuptools import setup

setup(
    name='gita',
    version='0.1dev',
    description='Manage multiple git repos',
    package=['gita',],
    author='Dong Zhou',
    author_email='zhou.dong@gmail.com',
    license='MIT',
    entry_points={
        'console_scripts':[
            'gita = gita.__main__.main'
            ]
        },
        )
