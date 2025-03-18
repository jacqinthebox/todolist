from setuptools import setup, find_packages

setup(
    name="todolist",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.68.0",
        "uvicorn>=0.15.0",
        "pydantic>=1.8.0",
    ],
    extras_require={
        "azure": [
            "azure-data-tables>=12.0.0",
            "azure-identity>=1.10.0"
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "httpx>=0.23.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "todolist=todolist.__main__:main",
            "todo=todolist.cli:main",
        ],
    },
)