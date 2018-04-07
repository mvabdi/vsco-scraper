# VSCO Scrape

Allows for easy scraping of one VSCO at a time

## Getting Started

Usage and installation of vsco-scraper

### Prerequisites

[Python 3](https://www.python.org/downloads/) is required. [Python 2](https://www.python.org/downloads/) is not supported.

### Installing

To install vsco-scraper:

```
 $ pip install vsco-scraper
```

To update vsco-scraper

```
 $ pip install vsco-scraper --upgrade
```


## Usage

To scrape a VSCO:
```
 $ vsco-scraper <username> --getImages
```
*Images are downloaded into the* `<current directory/<username>`

To scrape a user's journal on VSCO:
```
 $ vsco-scraper <username> --getJournal
```
*Journal Images are downloaded into the* `<current directory>/<username>/journal/<journalname>`
To scrape multiple VSCOs:
```
 $ vsco-scraper <filename-of-text-file> --multiple
```
*The scraper will read a text file, one username per line



## Options

Option | Secondary Options | Description
------ | ------------- | -----------
--getImages | -i | Grabs all of the user's images
--getJournal | -j | Grab's all of the images in the user's journals, then seperates into seperate folders
--multiple | -m | Grab's multple user's images


## Author

* **Mustafa Abdi** - *Initial work* - [mvabdi](https://github.com/mvabdi)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* instagram-scraper for inspiration

