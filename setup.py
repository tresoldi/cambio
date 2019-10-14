import pathlib
from setuptools import setup

# The directory containing this file
LOCAL_PATH = pathlib.Path(__file__).parent

# The text of the README file
README_FILE = (LOCAL_PATH / "README.md").read_text()

# This call to setup() does all the work
setup(
    name="cambio",
    version="0.0.1dev",
    description="Library for dealing with sound changes",
    long_description=README_FILE,
    long_description_content_type="text/markdown",
    url="https://github.com/tresoldi/cambio",
    author="Tiago Tresoldi",
    author_email="tresoldi@shh.mpg.de",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries",
    ],
    packages=["cambio"],
    package_data={'':"*.tsv"},
    keywords=["sound change", "phonology", "phonetics", "Lautwandel"],
    include_package_data=True,
    install_requires=["pyclts"],
    entry_points={"console_scripts": ["cambio=cambio.__main__:main"]},
    test_suite="tests",
    tests_require=[],
    zip_safe=False,
)
