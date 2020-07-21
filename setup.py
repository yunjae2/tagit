import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
        name = "edms-yunjae2",
        version = "0.0.1",
        author = "Yunjae Lee",
        author_email = "lyj7694@gmail.com",
        description = "Experiment data management system",
        long_description = long_description,
        long_description_content_type = "text/markdown",
        url = "https://github.com/yunjae2/edms",
        packages = setuptools.find_packages(),
        classifiers = [
            "Programming Language :: Python :: 3",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
        ],
        python_requires = '>=3.6',
)
