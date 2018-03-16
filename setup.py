"""
Generate static documentation for your Elm project.
"""
import sys
from setuptools import find_packages, setup
from setuptools.extension import Extension

if sys.platform == 'darwin':
    from distutils import sysconfig
    vars = sysconfig.get_config_vars()
    vars['LDSHARED'] = vars['LDSHARED'].replace('-bundle', '-dynamiclib')

ext = Extension('overlay_elm_package', sources=['src/elm_doc/native/overlay_elm_package.c'], libraries=["dl"])

setup(
    name='elm-doc',
    version='0.3.2',
    url='https://github.com/ento/elm-doc',
    license='BSD 3-clause',
    author='Marica Odagaki',
    author_email='ento.entotto@gmail.com',
    description='Generate static documentation for your Elm project',
    long_description=__doc__,
    zip_safe=False,
    platforms='any',
    install_requires=[
        'click',
        'doit',
        'python-magic',
        'retrying',
        'typing ; python_version < "3.5"',
    ],
    packages=find_packages('src', exclude=['tests']),
    package_dir={'': 'src'},
    package_data={'': ['elm_doc/native/*.js']},
    include_package_data=True,
    ext_modules=[ext],
    entry_points={
        'console_scripts': [
            'elm-doc = elm_doc.cli:main',
        ],
    },
    classifiers=[
        # As from http://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 3 - Alpha',
        #'Development Status :: 4 - Beta',
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
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Software Development :: Documentation',
    ]
)
