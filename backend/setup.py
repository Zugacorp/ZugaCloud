from setuptools import setup, find_packages

setup(
    name="zugacloud-backend",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "flask>=2.3.3",
        "flask-cors>=4.0.0",
        "boto3>=1.28.44",
        "botocore>=1.31.44",
        "python-jose[cryptography]>=3.3.0",
        "cryptography>=44.0.0",
        "requests>=2.32.3",
        "Authlib>=1.3.0",
        "python-dotenv>=1.0.0",
        "Werkzeug>=2.3.7",
        "watchdog>=3.0.0",
        "psutil>=5.9.8",
    ],
    python_requires=">=3.8",
) 