import os
from setuptools import setup, find_packages

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='django-statsd',
    version='0.1',
    description='',
    long_description=read('README.rst'),
    author='Andy McKay',
    author_email='andym@mozilla.com',
    license='BSD',
    packages=['django_statsd'],
    url='',
    package_data = {'django_statsd': ['templates/django_statsd/*.html']},
    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Framework :: Django'
        ],
    )
