"""
Generate static documentation for your Elm application.
"""
import sys
from setuptools import find_packages, setup


setup(
    name='elm-doc',
    version='1.0.0b1',
    url='https://github.com/ento/elm-doc',
    license='BSD 3-clause',
    author='Marica Odagaki',
    author_email='ento.entotto@gmail.com',
    description='Generate static documentation for your Elm application',
    long_description=__doc__,
    zip_safe=False,
    platforms='any',
    install_requires=[
        'click',
        'dirsync',
        'doit',
        'parsy',
        'requests',
        'retrying',
    ],
    packages=find_packages('src', exclude=['tests']),
    package_dir={'': 'src'},
    package_data={'': ['elm_doc/assets/assets.tar.gz']},
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'elm-doc = elm_doc.cli:main',
        ],
    },
    python_requires='>=3.5',
    classifiers=[
        # As from http://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 4 - Beta',
        # 'Development Status :: 5 - Production/Stable',
        # 'Development Status :: 6 - Mature',
        # 'Development Status :: 7 - Inactive',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX',
        'Operating System :: MacOS',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Software Development :: Documentation',
    ]
)
