import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="balaban",
    version="0.0.1",
    author="Will Thomson",
    author_email="willthomson1991@gmail.com",
    description="Bayesian hierarchical models for football",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/anenglishgoat/balaban",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_data={
        'font': ['JosefinSans-Regular.tff'],
},
    python_requires='>=3.2',
)