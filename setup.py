from setuptools import setup, find_packages

setup(
    name="vsco-scraper",
    version='0.51',
    description='Allows for a user to scrape users VSCOs',
    author='Mustafa Abdi',
    author_email='mustafabyabdi@gmail.com',
    packages=find_packages(),
    url='https://github.com/mvabdi/vsco-scraper',
    install_requires=[
        'tqdm',
        'requests',
        'beautifulsoup4',
    ],
    entry_points='''
        [console_scripts]
        vsco-scraper=vscoscrape:main
    ''',
    keywords='vsco scrape image images download',
)
