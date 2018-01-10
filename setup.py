import re
from setuptools import setup, find_packages


# Get version without importing, which avoids dependency issues
def get_version():
    with open('polygon_geohasher/version.py') as version_file:
        return re.search(r"""__version__\s+=\s+(['"])(?P<version>.+?)\1""",
                         version_file.read()).group('version')


def readme():
    with open('README.md') as f:
        return f.read()


install_requires = ['shapely', 'python-geohash']

setup(
    name='polygon-geohasher',
    version=get_version(),
    author='Alberto Bonsanto',
    author_email='',
    url='https://github.com/Bonsanto/polygon-geohasher',
    description='Wrapper over Shapely that returns the set of geohashes that form a Polygon',
    long_description=readme(),
    license='MIT',
    packages=find_packages(),
    install_requires=install_requires,
    include_package_data=False,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    keywords=['polygon', 'geohashes'],
)
