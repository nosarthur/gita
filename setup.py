from setuptools import setup

setup(
    name='gita',
    version='0.1.dev0',
    description='Manage multiple git repos',
    packages=['gita',],
    url='https://github.com/nosarthur/gita.git',
    author='Dong Zhou',
    author_email='zhou.dong@gmail.com',
    license='MIT',
    entry_points={
        'console_scripts':[
            'gita = gita.__main__:main'
            ]
        },
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Development Status :: 2 - Pre-Alpha",
        "License :: OSI Approved :: MIT License",
        ],
)
