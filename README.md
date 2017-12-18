# VSCO Scrape

Allows for easy scraping of one VSCO at a time + plotting location data of images

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

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
*Images are downloaded into the current directory/<username>*

To scrape a user's journal on VSCO:
```
 $ vsco-scraper <username> --getJournal
```
*Journal Images are downloaded into the current directory/<username>/journal/<journalname>*

To plot all images with locations to a Google Maps file:
```
 $ vsco-scraper <username> --plot
```
*Google maps HTML with plotted coordinates*

## Options

Option | Description
------ | -----------
--getImages or -i | Grabs all of the user's images
--getJournal or -j | Grab's all of the images in the user's journals, then seperates into seperate folders
--plot or -p | Plot's a map of the images with location coords


## Author

* **Mustafa Abdi** - *Initial work* - [mvabdi](https://github.com/mvabdi)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* instagram-scraper for inspiration

