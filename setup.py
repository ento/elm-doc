"""
Generate your own Elm package documentation site
"""
import sys
from setuptools import find_packages, setup
from setuptools.extension import Extension

if sys.platform == 'darwin':
    from distutils import sysconfig
    vars = sysconfig.get_config_vars()
    vars['LDSHARED'] = vars['LDSHARED'].replace('-bundle', '-dynamiclib')

ext = Extension('overlay_elm_package', sources=['native/overlay_elm_package.c'], libraries=["dl"])

with open('requirements.in') as f:
    dependencies = f.readlines()

setup(
    name='elm-doc',
    version='0.1.0',
    url='https://github.com/ento/elm-doc',
    license='BSD',
    author='Marica Odagaki',
    author_email='ento.entotto@gmail.com',
    description='Generate your own Elm package documentation site',
    long_description=__doc__,
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=dependencies,
    ext_modules=[ext],
    entry_points={
        'console_scripts': [
            'elm-doc = elm_doc.cli:main',
        ],
    },
    classifiers=[
        # As from http://pypi.python.org/pypi?%3Aaction=list_classifiers
        # 'Development Status :: 1 - Planning',
        # 'Development Status :: 2 - Pre-Alpha',
        # 'Development Status :: 3 - Alpha',
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
        'Programming Language :: Python :: 3 Only',
        'Topic :: Software Development :: Documentation',
    ]
)
