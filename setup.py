from setuptools import setup, find_packages

setup(
    name          = "pystates",
    version       = "0.4",
    url           = "http://wiki.github.com/egradman/pystates",
    author        = "Eric Gradman",
    author_email  = "eric@gradman.com",
    description   = "A simple and powerful python state machine framework using coroutines",
    license       = "MIT",
    packages      = find_packages(),
)
