#!/usr/bin/python

from distutils.core import setup

setup(name = "ip_info",
      version = "1.0",
      author = "Dennis Kaarsemaker",
      author_email = "dennis@kaarsemaker.net",
      url = "http://github.com/seveas/ip_info",
      description = "Simple IP information webapp",
      py_modules = ["ip_info"],
      classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Topic :: System :: Networking',
      ]
)
