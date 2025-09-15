"""
Setup configuration for ADK A2A System

Install with: pip install -e .
"""

from pathlib import Path

from setuptools import find_packages, setup

# Read requirements
def read_requirements(filename):
    """Read requirements from file."""
    req_file = Path(__file__).parent / filename
    if req_file.exists():
        with open(req_file) as f:
            return [
                line.strip()
                for line in f
                if line.strip() and not line.startswith("#")
            ]
    return []


# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = ""
if readme_file.exists():
    with open(readme_file, encoding="utf-8") as f:
        long_description = f.read()


setup(
    name="presentationpro-adk",
    version="2.0.0",
    author="PresentationPro Team",
    author_email="team@presentationpro.ai",
    description="A2A-enabled presentation generation system using Google ADK",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/presentationpro/adk-system",
    packages=find_packages(exclude=["tests", "tests.*", "docs", "docs.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    install_requires=read_requirements("requirements-base.txt"),
    extras_require={
        "dev": read_requirements("requirements-dev.txt"),
        "a2a": [
            "google-adk[a2a]>=1.0.0",
        ],
        "mcp": [
            "mcp>=0.1.0",
            "fastmcp>=0.1.0",
        ],
        "all": read_requirements("requirements-base.txt")
        + read_requirements("requirements-dev.txt"),
    },
    entry_points={
        "console_scripts": [
            "adk-server=app.main:main",
            "adk-migrate=scripts.migrate:main",
            "adk-test=scripts.test_system:main",
        ],
    },
    package_data={
        "": ["*.yaml", "*.json", "*.md"],
        "config": ["*.yaml", "*.json"],
        "static": ["*.html", "*.css", "*.js"],
    },
    include_package_data=True,
    zip_safe=False,
    project_urls={
        "Bug Reports": "https://github.com/presentationpro/adk-system/issues",
        "Source": "https://github.com/presentationpro/adk-system",
        "Documentation": "https://docs.presentationpro.ai",
    },
)