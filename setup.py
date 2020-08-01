from setuptools import find_packages, setup


setup(
    name='qx-base',
    version='1.0.0',
    author='Shawn',
    author_email='q-x64@live.com',
    url='https://github.com/qx-oo/qx-base/',
    description='Django base apps.',
    long_description=open("README.md").read(),
    packages=find_packages(exclude=["tests", ]),
    install_requires=[
        'Django >= 3.0',
        'djangorestframework >= 3.11.0',
        'djangorestframework-jwt >= 1.11.0',
        'PyCryptodome >= 3.9.8',
        'redis >= 3.5.3',
    ],
    python_requires='>=3.8',
    platforms='any',
)
