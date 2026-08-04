from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="shacl-to-datalog",
    version="1.0.0",
    description="A transpiler that converts SHACL constraints to Datalog queries",

    long_description_content_type="text/markdown",

    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "rdflib>=6.0.0",
        "pyshacl>=0.20.0",
        "SPARQLWrapper>=2.0.0",
        "requests>=2.25.0",
        "numpy>=1.20.0",
        "pandas>=1.3.0",
        "matplotlib>=3.3.0",
        "seaborn>=0.11.0",
        "tabulate>=0.8.0",
        "psutil>=5.8.0",
        "memory_profiler>=0.60.0"
    ],
    entry_points={
        "console_scripts": [
            "shacl2datalog=main:main",
            "run_experiments=run_experiments:main",
        ],
    },
)