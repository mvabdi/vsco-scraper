#!/usr/bin/env python3
import argparse
import concurrent.futures
import os
import json
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date
import requests

from tqdm import tqdm

from . import constants


THREADS = 5

class Scraper(object):
    def __init__(self, cache, latestCache):
        self.cache = cache
        self.latestCache = latestCache

    def get_user(self, username):
        """
        Gets the vsco user
        :params: username
        :return: none
        """
        self.username = username
        self.session = requests.Session()
        self.session.get(
            f"http://vsco.co/content/Static/userinfo?callback=jsonp_{str(round(time.time() * 1000))}_0",
            headers=constants.visituserinfo,
        )
        path = os.path.join(os.getcwd(), self.username)
        # If the path doesn't exist, then create it
        if not os.path.exists(path):
            os.makedirs(path)
        os.chdir(path)
        self.newSiteId()
        self.buildJSON()
        self.totalj = 0

    def newSiteId(self):
        """
        Gets the unique id used per vsco user, it can be found in the cookies
        :params: none
        :return: returns the site id of a user in case you were curious
        """
        if self.latestCache is not None:
            if self.username not in self.latestCache:
                self.latestCache[self.username] = {"images": {},
                    "collection": {},
                    "journal": {},
                    "profile": {},
                }
            elif "profile" not in self.latestCache[self.username]:
                self.latestCache[self.username]["profile"] = {}

        if self.cache is None or self.username not in self.cache:
            res = self.session.get(
                f"http://vsco.co/api/2.0/sites?subdomain={self.username}",
                headers=constants.visituserinfo,
            )
            self.siteid = res.json()["sites"][0]["id"]
            self.sitecollectionid = res.json()["sites"][0]["site_collection_id"]
            if self.cache is not None:
                self.cache[self.username] = [self.siteid, self.sitecollectionid]
        else:
            self.siteid = self.cache[self.username][0]
            self.sitecollectionid = self.cache[self.username][1]
        return self.siteid

    def buildJSON(self):
        """
        Creates the urls used to grab json data for a user
        :params: none
        :return: returns the main media url by default
        """
        self.mediaurl = f"http://vsco.co/api/2.0/medias?site_id={self.siteid}"
        self.journalurl = f"http://vsco.co/api/2.0/articles?site_id={self.siteid}"
        self.collectionurl = f"http://vsco.co/api/2.0/collections/{self.sitecollectionid}/medias?"
        self.profileurl = f"http://vsco.co/api/2.0/sites/{self.siteid}"

        return self.mediaurl

    def getProfile(self):
        """
        Downloads the profile pictures for the user
        :params: none
        :return: none
        """
        self.imagelist = []
        path = os.path.join(os.getcwd(), "profile")
        if not os.path.exists(path):
            os.makedirs(path)
        os.chdir(path)

        self.pbar = tqdm(
            desc=f"Finding if a new profile picture exists from {self.username}", unit=" post"
        )

        self.makeProfileList()

        self.pbar.close()

        self.pbar = tqdm(
                total=len(self.imagelist),
                desc=f"Downloading a new profile picture from {self.username}",
                unit=" post",
            )
        for lists in self.imagelist:
            try:
                self.download_img_normal(lists)
            except Exception as exc:
                print(f"{self.username} crached {exc}")
            self.pbar.update()
        self.pbar.close()
        os.chdir("..")

    def makeProfileList(self):
        """
        Creates a list holding data on the profile picture
        :params: none
        :return: a boolean on whether the list was successfully made
        """
        url = self.session.get(
            self.profileurl, 
            headers=constants.media).json()["site"]

        if self.latestCache is not None:
            if (
                url["profile_image_id"]
                in self.latestCache[self.username]["profile"]
            ):
                return True
            else:
                self.latestCache[self.username]["profile"][
                    url["profile_image_id"]
                ] = date.today().strftime("%m-%d-%Y")
        if (
            url["profile_image_id"] is None or
            f"{url['profile_image_id']}.jpg" in os.listdir()
        ):
            return True

        self.imagelist.append(
            [
                f"http://{url['responsive_url']}",
                url["profile_image_id"],
                False,
            ]
        )

        self.pbar.update()

        return True

    def getCollection(self):
        """
        Downloads the collection posts from the user
        :params: none
        :return: none
        """
        self.imagelist = []
        path = os.path.join(os.getcwd(), "collection")
        if not os.path.exists(path):
            os.makedirs(path)
        os.chdir(path)
        self.getCollectionList()
        with concurrent.futures.ThreadPoolExecutor(max_workers=THREADS) as executor:
            future_to_url = {
                executor.submit(self.download_img_normal, lists): lists
                for lists in self.imagelist
            }
            for future in tqdm(
                concurrent.futures.as_completed(future_to_url),
                total=len(self.imagelist),
                desc=f"Downloading collection posts from {self.username}",
                unit=" posts",
            ):
                liste = future_to_url[future]
                try:
                    data = future.result()
                except Exception as exc:
                    print(f"{liste} crashed {exc}")
        os.chdir("..")

    def getCollectionList(self):
        """
        Starts setting up to download the collection

        Does magical stuff with the concurrent future
        :params: none
        :return: none
        """
        self.pbar = tqdm(
            desc=f"Finding new collection posts from {self.username}", unit=" posts"
        )
        with ThreadPoolExecutor(max_workers=THREADS) as executor:
            future_to_url = {
                executor.submit(self.makeCollectionList, num): num for num in range(THREADS)
            }
            for future in concurrent.futures.as_completed(future_to_url):
                num = future_to_url[future]
                try:
                    data = future.result()
                except Exception as exc:
                    print(f"{num} crashed {exc}")
        self.pbar.close()

    def makeCollectionList(self, num):
        """
        Determines what file type a media item is, then appends the correct url
        :params: num - this does some magic, no idea why it works or why I did it
        :return: a boolean on whether the list was successfully made
        """
        num += 1
        z = self.session.get(
            self.collectionurl,
            params={"size": 100, "page": num},
            headers=constants.media,
        ).json()["medias"]

        count = len(z)
        while count > 0:
            for url in z:
                if self.latestCache is not None:
                    if (
                        str(url["upload_date"])[:-3]
                        in self.latestCache[self.username]["collection"]
                    ):
                        continue
                    else:
                        self.latestCache[self.username]["collection"][
                            str(url["upload_date"])[:-3]
                        ] = date.today().strftime("%m-%d-%Y")
                if (
                    f"{str(url['upload_date'])[:-3]}.jpg" in os.listdir()
                    or f"{str(url['upload_date'])[:-3]}.mp4" in os.listdir()
                ):
                    continue
                if url["is_video"] is True:
                    self.imagelist.append(
                        [
                            f"http://{url['video_url']}",
                            str(url["upload_date"])[:-3],
                            True,
                        ]
                    )
                    self.pbar.update()
                else:
                    self.imagelist.append(
                        [
                            f"http://{url['responsive_url']}",
                            str(url["upload_date"])[:-3],
                            False,
                        ]
                    )
                    self.pbar.update()
            num += THREADS
            z = self.session.get(
                self.collectionurl,
                params={"size": 100, "page": num},
                headers=constants.media,
            ).json()["medias"]
            count = len(z)
        return True

    def getJournal(self):
        """
        Downloads the journal posts from the user
        :params: none
        :return: none
        """
        self.getJournalList()
        self.progbarj = tqdm(
            total=self.totalj,
            desc=f"Downloading journal posts from {self.username}",
            unit=" posts",
        )
        for x in self.works:
            path = os.path.join(os.getcwd(), x[0])
            if not os.path.exists(path):
                os.makedirs(path)
            os.chdir(path)
            x.pop(0)
            with ThreadPoolExecutor(max_workers=THREADS) as executor:
                future_to_url = {
                    executor.submit(self.download_img_journal, part): part for part in x
                }
                for future in concurrent.futures.as_completed(future_to_url):
                    part = future_to_url[future]
                    try:
                        data = future.result()
                    except Exception as exc:
                        print(f"{part} crashed {exc}")
            os.chdir(os.path.normpath(os.getcwd() + os.sep + os.pardir))
        self.progbarj.close()

    def getJournalList(self):
        """
        Opens initial journal data of a user and creates the journal folder

        Then it does some magical bs, I made this years ago no idea how it works

        :params: none
        :return: none
        """
        self.works = []
        self.jour_found = self.session.get(
            self.journalurl, params={"size": 10000, "page": 1}, headers=constants.media
        ).json()["articles"]
        self.pbarjlist = tqdm(
            desc=f"Finding new journal posts from {self.username}", unit=" posts"
        )
        for x in self.jour_found:
            self.works.append([x["permalink"]])
        path = os.path.join(os.getcwd(), "journal")
        if not os.path.exists(path):
            os.makedirs(path)
        os.chdir(path)
        with ThreadPoolExecutor(max_workers=THREADS) as executor:
            future_to_url = {
                executor.submit(self.makeListJournal, len(self.jour_found), val): val
                for val in range(len(self.jour_found))
            }
            for future in concurrent.futures.as_completed(future_to_url):
                val = future_to_url[future]
                try:
                    data = future.result()
                except Exception as exc:
                    print(f"{val} crashed {exc}")
        self.pbarjlist.close()

    def makeListJournal(self, num, loc):
        """
        Makes the list of all journal entries on the users page
        :params: num, loc
        :return: a boolean on whether the journal media was able to be grabbed
        """
        for item in self.jour_found[loc]["body"]:
            if self.latestCache is not None:
                if item["type"] == "text":
                    if (
                        f"{str(item['content'])}.txt"
                        in self.latestCache[self.username]["journal"]
                    ):
                        continue
                    else:
                        self.latestCache[self.username]["images"][
                            f"{str(item['content'])}.txt"
                        ] = date.today().strftime("%m-%d-%Y")
                else:
                    if (
                        str(item["content"][0]["id"])
                        in self.latestCache[self.username]["journal"]
                    ):
                        continue
                    else:
                        self.latestCache[self.username]["journal"][
                            str(item["content"][0]["id"])
                        ] = date.today().strftime("%m-%d-%Y")

            if item["type"] == "image":
                if os.path.exists(
                    os.path.join(os.getcwd(), self.jour_found[loc]["permalink"])
                ):
                    if f"{str(item['content'][0]['id'])}.jpg" in os.listdir(
                        os.path.join(os.getcwd(), self.jour_found[loc]["permalink"])
                    ):
                        continue
                self.works[loc].append(
                    [
                        f"http://{item['content'][0]['responsive_url']}",
                        item["content"][0]["id"],
                        "img",
                    ]
                )
            elif item["type"] == "video":
                if os.path.exists(
                    os.path.join(os.getcwd(), self.jour_found[loc]["permalink"])
                ):
                    if f"{str(item['content'][0]['id'])}.mp4" in os.listdir(
                        os.path.join(os.getcwd(), self.jour_found[loc]["permalink"])
                    ):
                        continue
                self.works[loc].append(
                    [
                        f"http://{item['content'][0]['video_url']}",
                        item["content"][0]["id"],
                        "vid",
                    ]
                )
            elif item["type"] == "text":
                if os.path.exists(
                    os.path.join(os.getcwd(), self.jour_found[loc]["permalink"])
                ):
                    if f"{str(item['content'])}.txt" in os.listdir(
                        os.path.join(os.getcwd(), self.jour_found[loc]["permalink"])
                    ):
                        continue
                self.works[loc].append([item["content"], "txt"])
            self.totalj += 1
            self.pbarjlist.update()
        return True

    def download_img_journal(self, lists):
        """
        Downloads the journal media in specified ways depending on the type of media

        Since Journal items can be text files, images, or videos, I had to make 3
        different ways of downloading

        :params: lists - No idea why I named it this, but it's a media item
        :return: a boolean on whether the journal media was able to be downloaded
        """
        if lists[1] == "txt":
            with open(f"{str(lists[0])}.txt", "w") as file:
                file.write(lists[0])
        if lists[2] == "img":
            if f"{lists[1]}.jpg" in os.listdir():
                return True
            with open(f"{str(lists[1])}.jpg", "wb") as file:
                file.write(requests.get(lists[0], stream=True).content)

        elif lists[2] == "vid":
            if f"{lists[1]}.mp4" in os.listdir():
                return True
            with open(f"{str(lists[1])}.mp4", "wb") as file:
                for chunk in requests.get(lists[0], stream=True).iter_content(
                    chunk_size=1024
                ):
                    if chunk:
                        file.write(chunk)
        self.progbarj.update()
        return True

    def getImages(self):
        """
        Makes a list of all media items in a page

        I clearly recall straight copy pasting the concurrent futures thing from stack
        overflow. Still have no idea how it works

        :params: none
        :return: none
        """
        self.imagelist = []
        self.getImageList()
        with concurrent.futures.ThreadPoolExecutor(max_workers=THREADS) as executor:
            future_to_url = {
                executor.submit(self.download_img_normal, lists): lists
                for lists in self.imagelist
            }
            for future in tqdm(
                concurrent.futures.as_completed(future_to_url),
                total=len(self.imagelist),
                desc=f"Downloading posts from {self.username}",
                unit=" posts",
            ):
                liste = future_to_url[future]
                try:
                    data = future.result()
                except Exception as exc:
                    print(f"{liste} crashed {exc}")

    def getImageList(self):
        """
        tqdm is a great library isn't it

        :params: none
        :return: none
        """
        self.pbar = tqdm(desc=f"Finding new posts from {self.username}", unit=" posts")
        with ThreadPoolExecutor(max_workers=THREADS) as executor:
            future_to_url = {
                executor.submit(self.makeImageList, num): num for num in range(THREADS)
            }
            for future in concurrent.futures.as_completed(future_to_url):
                num = future_to_url[future]
                try:
                    data = future.result()
                except Exception as exc:
                    print(f"{num} crashed {exc}")
        self.pbar.close()

    def makeImageList(self, num):
        """
        At this point I'm only doing these comments out of a general sense I should comment
        all these functions after that one PR did it

        Don't ask me how it works, frankly I'm surprised it does

        :params: num
        :return: a boolean on whether the journal media was able to be grabbed
        """
        num += 1
        z = self.session.get(
            self.mediaurl, params={"size": 100, "page": num}, headers=constants.media
        ).json()["media"]
        count = len(z)
        while count > 0:
            for url in z:
                if self.latestCache is not None:
                    if (
                        str(url["upload_date"])[:-3]
                        in self.latestCache[self.username]["images"]
                    ):
                        continue
                    else:
                        self.latestCache[self.username]["images"][
                            str(url["upload_date"])[:-3]
                        ] = date.today().strftime("%m-%d-%Y")
                if (
                    f"{str(url['upload_date'])[:-3]}.jpg" in os.listdir()
                    or f"{str(url['upload_date'])[:-3]}.mp4" in os.listdir()
                ):
                    continue
                if url["is_video"] is True:
                    self.imagelist.append(
                        [
                            f"http://{url['video_url']}",
                            str(url["upload_date"])[:-3],
                            True,
                        ]
                    )
                    self.pbar.update()
                else:
                    self.imagelist.append(
                        [
                            f"http://{url['responsive_url']}",
                            str(url["upload_date"])[:-3],
                            False,
                        ]
                    )
                    self.pbar.update()
            num += THREADS
            z = self.session.get(
                self.mediaurl,
                params={"size": 100, "page": num},
                headers=constants.media,
            ).json()["media"]
            count = len(z)
        return True

    def download_img_normal(self, lists):
        """
        This function makes sense at least

        The if '%s.whatever' sections are to skip downloading the file again if it's already been downloaded

        At the time I wrote this, I only remember seeing that images and videos were the only things allowed

        So I didn't write an if statement checking for text files, so this would just skip it I believe if it ever came up
        and return True

        :params: lists - My naming sense was beat. lists is just a media item.
        :return: a boolean on whether the media item was downloaded successfully
        """
        if lists[2] is False:
            if f"{lists[1]}.jpg" in os.listdir():
                return True
            with open(f"{str(lists[1])}.jpg", "wb") as file:
                file.write(requests.get(lists[0], stream=True).content)
        else:
            if f"{lists[1]}.mp4" in os.listdir():
                return True
            with open(f"{str(lists[1])}.mp4", "wb") as file:
                for chunk in requests.get(lists[0], stream=True).iter_content(
                    chunk_size=1024
                ):
                    if chunk:
                        file.write(chunk)
        return True

    def run_all(self):
        """
        This runs all of the operations on a user's profile,
        it gets the images, the collection, and the journal entries
        :params: none
        :return: none
        """
        self.getImages()
        self.getCollection()
        self.getJournal()

    def run_all_profile(self):
        """
        This runs all of the operations on a user's profile,
        it gets the images, the collection, journal entries, and the profile pictures
        :params: none
        :return: none
        """
        self.run_all()
        self.getProfile()




def openCache(file_name):
    """
    This function is meant to open a self.cache for previously downloaded media / usernames
    :params: file the filename used to store the self.cache
    """
    with open(file_name, "a+", encoding="utf-8") as file:
        try:
            file.seek(0)
            cache = json.load(file)
        except Exception:
            cache = {}
        return cache

def updateCache(file_name, cache):
    """
    This function will update the latest self.cache with more information
    :params: file the filename used to store the self.cache
    """
    with open(file_name, "w", encoding="utf-8") as file:
        json.dump(cache, file, ensure_ascii=False, indent=4)

def multiplePeople(username, vsco, scraper, func):
    """
    This function will run the func with various usernames given
    :params: username, vsco, and func (callable function)
    """
    with open(username, "r") as file:
        y = [x.replace("\n", "") for x in file]
    for z in y:
        try:
            os.chdir(vsco)
            scraper.get_user(z)
            func(scraper)
            print()
        except:
            print(f"{z} crashed")
            pass
    os.chdir(vsco)

def parser():
    """Returns the parser arguments
    :params: none
    :return: parser.parse_args() object
    """
    parser = argparse.ArgumentParser(
        description="Scrapes a specified users VSCO Account"
    )
    parser.add_argument(
        "username",
        type=str,
        help="VSCO user to scrape or file name to read usernames off of. Filename feature works with -m, -mc, -mj, and -a only",
    )
    parser.add_argument(
        "-s", "--siteId", action="store_true", help="Grabs VSCO siteID for user"
    )
    parser.add_argument(
        "-i", "--getImages", action="store_true", help="Get the pictures of the user"
    )
    parser.add_argument(
        "-j",
        "--getJournal",
        action="store_true",
        help="Get the journal images of the user",
    )
    parser.add_argument(
        "-p",
        "--getProfilePicture",
        action="store_true",
        help="Get the profile picture of the user",
    )
    parser.add_argument(
        "-c",
        "--getCollection",
        action="store_true",
        help="Get the collection images of the user",
    )
    parser.add_argument(
        "-m", "--multiple", action="store_true", help="Scrape images from multiple users"
    )
    parser.add_argument(
        "-mj",
        "--multipleJournal",
        action="store_true",
        help="Scrape multiple users journal posts",
    )
    parser.add_argument(
        "-mc",
        "--multipleCollection",
        action="store_true",
        help="Scrape multiple users collection posts",
    )
    parser.add_argument(
        "-mp",
        "--multipleProfile",
        action="store_true",
        help="Scrape multiple users profile pictures",
    )
    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Scrape multiple users images, journals, and collections",
    )
    parser.add_argument(
        "-ap",
        "--allProfile",
        action="store_true",
        help="Scrape multiple users images, journals, collections, and profile pictures",
    )
    parser.add_argument(
        "-ch",
        "--cacheHit",
        action="store_true",
        help="Caches site id in case of a username switch",
    )
    parser.add_argument(
        "-l",
        "--latest",
        action="store_true",
        help="Only downloads media one time, and makes sure to self.cache the media",
    )
    return parser.parse_args()

def main():
    args = parser()
    vsco = os.getcwd()
    cache = {}
    latestCache = {}

    if args.latest:
        latestCache = openCache(args.username + "_latest_cache_store")

    if args.cacheHit:
        cache = openCache(args.username + "_cache_store")

    scraper = Scraper(cache, latestCache)
    if args.siteId:
        scraper.get_user(args.username)
        print(scraper.newSiteId())
        os.chdir(vsco)

    if args.getImages:
        scraper.get_user(args.username)
        scraper.getImages()
        os.chdir(vsco)

    if args.getJournal:
        scraper.get_user(args.username)
        scraper.getJournal()
        os.chdir(vsco)

    if args.getCollection:
        scraper.get_user(args.username)
        scraper.getCollection()
        os.chdir(vsco)

    if args.getProfilePicture:
        scraper.get_user(args.username)
        scraper.getProfile()
        os.chdir(vsco)

    if args.multiple:
        multiplePeople(args.username, vsco, scraper, Scraper.getImages)

    if args.multipleJournal:
        multiplePeople(args.username, vsco, scraper, Scraper.getJournal)

    if args.multipleCollection:
        multiplePeople(args.username, vsco, scraper, Scraper.getCollection)

    if args.multipleProfile:
        multiplePeople(args.username, vsco, scraper, Scraper.getProfile)

    if args.all:
        multiplePeople(args.username, vsco, scraper, Scraper.run_all)

    if args.allProfile:
        multiplePeople(args.username, vsco, scraper, Scraper.run_all_profile)

    if args.cacheHit:
        updateCache(args.username + "_cache_store", scraper.cache)

    if args.latest:
        updateCache(args.username + "_latest_cache_store", scraper.latestCache)


if __name__ == "__main__":
    main()
