import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = f.read().splitlines()

setuptools.setup(
    name="NetScanOrchestrator",
    version="0.1.0",
    author="AI Developer", # Or a more specific name/email
    author_email="ai.dev@example.com",
    description="A parallel Nmap scanner with a web UI and database logging",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="<your-repository-url-here>", # Placeholder for actual repo URL
    project_urls={
        "Bug Tracker": "<your-issue-tracker-url-here>",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License", # Assuming MIT, update if different
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Topic :: Security",
        "Topic :: System :: Networking :: Monitoring",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.7", # Based on common practice, adjust if specific features need newer versions
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'netscan=cli.main:app',
        ],
    },
    include_package_data=True, # To include non-code files specified in MANIFEST.in (if you add one) or by SCM integration
)
