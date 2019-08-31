"""
Quart-Minify
-------------

A Quart extension to minify quart response for html,
javascript, css and less compilation as well.

"""
from setuptools import setup

setup(
    name='quart-minify',
    version='0.1.0',
    url='https://github.com/AceFire6/quart_minify/',
    download_url='https://github.com/AceFire6/quart_minify/archive/0.1.0.tar.gz',
    license='MIT',
    author='Mohamed Feddad <mrf345@gmail.com>, Jethro Muller <git@jethromuller.co.za>',
    description='flask extension to minify html, css, js and less',
    long_description=__doc__,
    py_modules=['minify'],
    packages=['quart_minify'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    keywords=['quart', 'extension', 'minifer', 'htmlmin', 'lesscpy', 'jsmin', 'html', 'js', 'less', 'css'],
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    install_requires=[
        'htmlmin>=0.1.12,<0.2.0',
        'jsmin>=2.2,<2.3',
        'lesscpy>=0.13.0,<0.14.0',
        'quart>=0.10.0,<0.11.0',
    ],
    test_requires=[
        'pytest>=5.1,<6.0',
        'pytest-asyncio>=0.10.0,<0.11.0',
    ],
    setup_requires=['pytest-runner'],
)
