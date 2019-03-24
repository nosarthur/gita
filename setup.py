from setuptools import setup

long_description = None
with open('README.md') as f:
    long_description = f.read()

setup(
    name='gita',
    packages=['gita'],
    version='0.8.7',
    license='MIT',
    description='Manage multiple git repos',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/nosarthur/gita',
    platforms=['linux', 'osx', 'win32'],
    keywords=['git', 'manage multiple repositories'],
    author='Dong Zhou',
    author_email='zhou.dong@gmail.com',
    entry_points={'console_scripts': ['gita = gita.__main__:main']},
    install_requires=['pyyaml>=5.1'],
    python_requires='~=3.6',
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Topic :: Software Development :: Version Control :: Git",
        "Topic :: Terminals",
        "Topic :: Utilities",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    include_package_data=True,
)
