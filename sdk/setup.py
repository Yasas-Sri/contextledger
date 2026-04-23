from setuptools import setup, find_packages

setup(
    name="contextledger-client",
    version="1.0.0",
    description="Python client SDK for ContextLedger Lite — shared AI agent memory",
    packages=find_packages(),
    install_requires=["httpx>=0.27.0"],
    python_requires=">=3.11",
)