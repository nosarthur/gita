from setuptools import setup

long_description = None
with open('README.md') as f:
    long_description = f.read()

setup(
    name='gita',
    packages=['gita'],
    version='0.7.6',
    description='Manage multiple git repos',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/nosarthur/gita',
    keywords=['git', 'manage multiple repositories'],
    author='Dong Zhou',
    author_email='zhou.dong@gmail.com',
    license='MIT',
    entry_points={'console_scripts': ['gita = gita.__main__:main']},
    install_requires=['pyyaml>=3.13'],
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
    ],
    include_package_data=True,
)
