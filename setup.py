from setuptools import find_packages, setup

setup(
    name="MarketPulse",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "google-genai",
        "schedule",
        "python-dotenv",
        "requests",
    ],
    python_requires=">=3.10",
)
