import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="balaban-anenglishgoat",
    version="0.0.1",
    author="Will Thomson",
    author_email="willthomson1991@gmail.com",
    description="Bayesian hierarchial models for football",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/anenglishgoat/balaban",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.2',
)