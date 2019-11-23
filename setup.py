import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyce3",
    version="1.0.0",
    author="Zhanliang Liu",
    author_email="liang@zliu.org",
    description="Multilingual Web Page Content Extractor",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/liuzl/pyce3",
    packages=setuptools.find_packages(),
    py_modules=['pyce3'],
    install_requires=[
        "chardet",
        "python-dateutil",
        "lxml"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
