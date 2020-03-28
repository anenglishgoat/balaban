import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="balaban",
    version="0.0.20",
    author="Will Thomson",
    author_email="willthomson1991@gmail.com",
    description="Bayesian hierarchical models for football",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/anenglishgoat/balaban",
    packages=setuptools.find_packages(),
    install_requires=['importlib.resources', 'numpy', 'pymc3', 'pandas', 'matplotlib','selenium'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    include_package_data=True,
    python_requires='>=3.2',
)