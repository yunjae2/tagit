import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
        name = "etagit",
        version = "0.0.9",
        author = "Yunjae Lee",
        author_email = "lyj7694@gmail.com",
        description = "CLI tagging system for experiments",
        long_description = long_description,
        long_description_content_type = "text/markdown",
        url = "https://github.com/yunjae2/tagit",
        packages = setuptools.find_packages(exclude=['test']),
        classifiers = [
            "Programming Language :: Python :: 3",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
        ],
        entry_points = {
            "console_scripts": ["tagit=tagit.main:main"],
        },
        python_requires = '>=3.6',
)
