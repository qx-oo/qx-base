from setuptools import find_packages, setup


setup(
    name='qx-base',
    version='1.0.7',
    author='Shawn',
    author_email='q-x64@live.com',
    url='https://github.com/qx-oo/qx-base/',
    description='Django base apps.',
    long_description=open("README.md").read(),
    packages=find_packages(exclude=["tests", "qx_test"]),
    install_requires=[
        'Django >= 2.2',
        'djangorestframework >= 3.10',
        'djangorestframework-jwt >= 1.11.0',
        'PyCryptodome >= 3.9',
        'redis >= 3.3',
        'psycopg2 >= 2.8.3',
    ],
    python_requires='>=3.7',
    platforms='any',
)
