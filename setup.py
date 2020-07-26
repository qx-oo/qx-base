from setuptools import find_packages, setup


setup(
    name='qx-user',
    version='1.0.0',
    # license='',
    author='Shawn',
    author_email='q-x64@live.com',
    url='https://github.com/qx-oo/qx-user/',
    description='Django user apps.',
    # long_description=open("README.md").read(),
    packages=find_packages(exclude=["tests", ]),
    install_requires=[
        'Django >= 3.0',
        'djangorestframework >= 3.11.0',
        'djangorestframework-jwt >= 1.11.0',
        'pycrypto >= 2.6.1',
    ],
    python_requires='>=3.8',
    platforms='any',
)
