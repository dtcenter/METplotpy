import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="metplotpy",
    version="1.0.0-beta2",
    author="METplus",
    author_email="met-help@ucar.edu",
    description="plotting package for METplus",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dtcenter/METplotpy",
    packages=setuptools.find_packages(),
    classifiers=[
         "Programming Language :: Python :: 3",
         "License :: Apache LICENSE-2.0",
         "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
