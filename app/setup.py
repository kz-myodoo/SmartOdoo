from pathlib import Path

from setuptools import find_packages, setup


ROOT = Path(__file__).resolve().parent
README = ROOT / "readme.md"


setup(
    name="smartodoo",
    version="2.4",
    description="SmartOdoo project tools",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.10",
)
