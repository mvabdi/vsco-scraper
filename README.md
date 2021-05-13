# VSCO Scraper

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

To update vsco-scraper:

```
 $ pip install vsco-scraper --upgrade
```

## Usage

To scrape a VSCO:

```
 $ vsco-scraper <username> --getImages
```

_Images are downloaded into the_ `<current directory/<username>`

To scrape a user's journal on VSCO:

```
 $ vsco-scraper <username> --getJournal
```

_Journal Images are downloaded into the_ `<current directory>/<username>/journal/<journalname>`

To scrape a user's collection on VSCO:

```
 $ vsco-scraper <username> --getCollection
```

_Collection Images are downloaded into the_ `<current directory>/<username>/collection>`

To scrape multiple VSCOs:

```
 $ vsco-scraper <filename-of-text-file> --multiple
```

\*The scraper will read a text file, one username per line

To scrape multiple VSCOs images, journals and collections:

```
 $ vsco-scraper <filename-of-text-file> --all
```

\*Same as above one username per line, but will also download journals and collection if it finds them

## Options

| Option               | Secondary Options | Description                                                                                                   |
| -------------------- | ----------------- | ------------------------------------------------------------------------------------------------------------- |
| --getImages          | -i                | Grabs all of the user's images                                                                                |
| --getJournal         | -j                | Grabs all of the images in the user's journals, then separates into separate folders                          |
| --getCollection      | -c                | Grabs all of the images in the user's collection                                                              |
| --multiple           | -m                | Grab's multiple user's images                                                                                 |
| --multipleJournal    | -mj               | Grab's multiple user's journals                                                                               |
| --multipleCollection | -mc               | Grab's multiple user's collections                                                                            |
| --all                | -a                | Scrape multiple users journals, collections and images, will download journal and collection if they have one |

## Author

- **Mustafa Abdi** - _Initial work_ - [mvabdi](https://github.com/mvabdi)

## Contributors

- ** Hadjer Benzaamia ** - _Collection PR_ - [bz-hadjer](https://github.com/bz-hadjer)
- ** sc1341 ** - _Pull Request_ - [sc1341](https://github.com/sc1341)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

- instagram-scraper for inspiration
