from setuptools import setup


setup(
    # Because django-statsd was taken, I called this django-statsd-mozilla.
    name='django-statsd-mozilla',
    version='0.3.16',
    description='Django interface with statsd',
    long_description=open('README.rst').read(),
    author='Andy McKay',
    author_email='andym@mozilla.com',
    license='BSD',
    install_requires=['statsd==2.1.2'],
    packages=['django_statsd',
              'django_statsd/patches',
              'django_statsd/clients',
              'django_statsd/loggers',
              'django_statsd/management',
              'django_statsd/management/commands'],
    url='https://github.com/andymckay/django-statsd',
    entry_points={
        'nose.plugins.0.10': [
            'django_statsd = django_statsd:NoseStatsd'
        ]
    },
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Framework :: Django'
    ]
)
