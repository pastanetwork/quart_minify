import setuptools


with open("README.md") as readme_file:
    long_description = readme_file.read()

setuptools.setup(
    name="quart-minify",
    version="0.5.0",
    author="Jethro Muller",
    author_email="git@jethromuller.co.za",
    description="Quart extension to minify HTML, CSS, JS, and less",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/AceFire6/quart_minify/",
    download_url="https://github.com/AceFire6/quart_minify/archive/0.1.0.tar.gz",
    packages=setuptools.find_packages(),
    python_requires=">=3.7",
    license="MIT",
    py_modules=["minify"],
    zip_safe=False,
    include_package_data=True,
    platforms="any",
    project_urls={"Source": "https://github.com/AceFire6/quart_minify/"},
    keywords="quart extension minifer htmlmin lesscpy jsmin html js less css",
    classifiers=[
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    install_requires=[
        "htmlmin>=0.1.12",
        "jsmin>=3.0",
        "lesscpy>=0.13.0",
        "quart>=0.10.0",
    ],
    tests_require=[
        "pytest>=5.1,<6.0",
        "pytest-asyncio>=0.10.0,<0.11.0",
        "flake8>=3.7,<3.8",
        "flake8-quotes>=2.1,<2.2",
    ],
)
