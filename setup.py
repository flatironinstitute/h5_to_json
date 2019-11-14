import setuptools

pkg_name = "h5_to_json"

setuptools.setup(
    name=pkg_name,
    version="0.1.5",
    author="Jeremy Magland",
    description="Represent .hdf5 files in .json format - derived from https://github.com/HDFGroup/hdf5-json",
    packages=setuptools.find_packages(),
    scripts=[
        'bin/h5_to_json',
        'bin/json_to_h5'
    ],
    install_requires=[],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ]
)
