from setuptools import setup
setup(
    name='twine-select',
    version='1.0',
    installs_requires=[
        'twine>=2; python_version>="3.6"',
        'twine<2; python_version<"3.6"',
    ],
)
