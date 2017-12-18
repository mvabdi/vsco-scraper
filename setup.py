from setuptools import setup, find_packages

setup(
    name="vsco-scrape",
    version='0.1',
    descripton='Allows for a user to scrape one VSCO user at a time',
    author='Mustafa Abdi',
    author_email='mustafabyabdi@gmail.com',
    packages=find_packages(),
    
    install_requires=[
        'tqdm>=4.19.4',
        'requests>=2.18.4',
        'geocoder>=1.33.0',
        'gmplot>=1.2.0',
        'beautifulsoup4',
    ],
    entry_points='''
        [console_scripts]
        vsco-scrape=vscoscrape:main
    ''',
    keywords='vsco scrape image images',
)
