from setuptools import setup, find_packages


def readme() -> str:
    with open("README.md") as f:
        return f.read()


def requirements() -> str:
    with open("requirements.txt") as f:
        return f.read()


setup(
    name="polygon-geohasher",
    author="Alberto Bonsanto",
    author_email="",
    url="https://github.com/Bonsanto/polygon-geohasher",
    description="Wrapper over Shapely that returns the set of geohashes that form a Polygon",
    long_description=readme(),
    license="MIT",
    packages=find_packages(),
    package_data={"": ["py.typed"]},
    install_requires=requirements(),
    include_package_data=False,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
    ],
    keywords=["polygon", "geohashes"],
)
