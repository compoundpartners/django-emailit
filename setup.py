from setuptools import setup, find_packages

from mandrillit import __version__


setup(
    name="js-mandrillit",
    version=__version__,
    url='http://github.com/compoundpartners/js-mandrillit',
    license='BSD',
    platforms=['OS Independent'],
    description="Make sending mandrill emails easy.",
    long_description=open('README.rst').read(),
    author='Compound Partners Ltd',
    author_email='hello@compoundpartners.co.uk',
    packages=find_packages(),
    install_requires=(
        'Django>=1.11',
        'premailer>=1.12',
        'django-absolute',
        'mandrill',
    ),
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
    ],
)
