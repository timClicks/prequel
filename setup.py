#!/usr/bin/env python

from distutils.core import setup

with open("README.md") as f:
  long_desc = f.read()

setup(name='prequel',
      version='0.1',
      description='Gets your data into a database',
      author='Tim McNamara',
      author_email='code@timmcnamara.co.nz',
      long_description=long_desc,
      url='https://github.com/timClicks/prequel',
      packages=['prequel'],
      classifiers=[
                   'Development Status :: 2 - Pre-Alpha',
                   'Environment :: Console',
                   'Intended Audience :: End Users/Desktop',
                   'Intended Audience :: Education',
                   'Intended Audience :: Healthcare Industry',
                   'Intended Audience :: Science/Research',
                   'License :: OSI Approved :: Apache Software License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Topic :: Database',
                   'Topic :: Scientific/Engineering',
                   'Topic :: Scientific/Engineering :: Information Analysis',
                   'Topic :: Utilities'
      ]
     )