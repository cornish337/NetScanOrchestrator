import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = f.read().splitlines()

setuptools.setup(
    name="parallel_nmap_scanner",
    version="0.1.0",
    author="AI Developer", # Or a more specific name/email
    author_email="ai.dev@example.com",
    description="A parallel Nmap scanner with a web UI",
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
            'parallel-nmap-scanner=nmap_parallel_scanner:main', # Assuming your main CLI script is nmap_parallel_scanner.py and has a main()
            'netscan=netscan.cli:main',
        ],
        'gui_scripts': [
            'parallel-nmap-scanner-ui=web_ui.app:main', # Or however the Flask app is meant to be launched if not just `flask run`
        ],
    },
    include_package_data=True, # To include non-code files specified in MANIFEST.in (if you add one) or by SCM integration
    # If you have data files within your packages (e.g. src/your_package/data_file.dat)
    # package_data={
    # 'your_package': ['data_file.dat'],
    # },
    # If you have data files outside your packages but you want to include them in the wheel/sdist
    # data_files=[('my_data', ['data/data_file'])],
)
