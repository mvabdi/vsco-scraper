from setuptools import find_packages, setup


setup(
    name="vsco-scraper",
    version="0.60",
    description="Scrape a user's VSCO profile data",
    author="Mustafa Abdi",
    author_email="mustafabyabdi@gmail.com",
    packages=find_packages(),
    url="https://github.com/mvabdi/vsco-scraper",
    install_requires=[
        "tqdm",
        "requests",
        "beautifulsoup4",
    ],
    entry_points="""
        [console_scripts]
        vsco-scraper=vscoscrape:main
    """,
    keywords="vsco scrape image images download",
)
