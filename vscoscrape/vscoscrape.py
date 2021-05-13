#!/usr/bin/env python3
import argparse
import concurrent.futures
import os
import random
import time
from concurrent.futures import ThreadPoolExecutor

import requests

from tqdm import tqdm

from . import constants


class Scraper(object):

    def __init__(self, username):
      self.username = username
      self.session = requests.Session()
      self.session.get("http://vsco.co/content/Static/userinfo?callback=jsonp_%s_0"% (str(round(time.time()*1000))),headers=constants.visituserinfo)
      self.uid = self.session.cookies.get_dict()['vs']
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
        res = self.session.get("http://vsco.co/ajxp/%s/2.0/sites?subdomain=%s" % (self.uid,self.username))
        self.siteid = res.json()["sites"][0]["id"]
        self.sitecollectionid = res.json()["sites"][0]["site_collection_id"]
        return self.siteid

    def buildJSON(self):
        """
        Creates the urls used to grab json data for a user
        :params: none
        :return: returns the main media url by default
        """
        self.mediaurl = "http://vsco.co/ajxp/%s/2.0/medias?site_id=%s" % (self.uid,self.siteid)
        self.journalurl = "http://vsco.co/ajxp/%s/2.0/articles?site_id=%s" % (self.uid,self.siteid)
        self.collectionurl = "http://vsco.co/ajxp/%s/2.0/collections/%s/medias?" % (self.uid,self.sitecollectionid)
        return self.mediaurl

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
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_url = {executor.submit(self.download_img_normal,lists): lists for lists in self.imagelist}
            for future in tqdm(concurrent.futures.as_completed(future_to_url), total=len(self.imagelist), desc='Downloading collection posts of %s'%self.username, unit=' posts'):
                liste = future_to_url[future]
                try:
                    data=future.result()
                except Exception as exc:
                    print('%r crashed %s' % (liste,exc))
        os.chdir('..')


    def getCollectionList(self):
        """
        Starts setting up to download the collection

        Does magical stuff with the concurrent future
        :params: none
        :return: none
        """
        self.pbar = tqdm(desc='Finding new collection posts of %s' %self.username, unit=' posts')
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_url = {executor.submit(self.makeCollectionList,num): num for num in range(5)}
            for future in concurrent.futures.as_completed(future_to_url):
                num=future_to_url[future]
                try:
                    data=future.result()
                except Exception as exc:
                    print('%r crashed %s' % (num,exc))
        self.pbar.close()

        
    def makeCollectionList(self, num):
        """
        Determines what file type a media item is, then appends the correct url
        :params: num - this does some magic, no idea why it works or why I did it
        :return: a boolean on whether the list was successfully made
        """
        num +=1
        z = self.session.get(self.collectionurl,params={"size":100,"page":num},headers=constants.media).json()['medias']

        count = len(z)
        while count>0:
            for url in z:
                if '%s.jpg' % str(url["upload_date"])[:-3] in os.listdir() or '%s.mp4' % str(url["upload_date"])[:-3] in os.listdir():
                    continue
                if url['is_video'] is True:
                    self.imagelist.append(["http://%s"% url["video_url"],str(url["upload_date"])[:-3],True])
                    self.pbar.update()
                else:
                    self.imagelist.append(["http://%s"% url["responsive_url"],str(url["upload_date"])[:-3],False])
                    self.pbar.update()
            num +=5
            z = self.session.get(self.collectionurl,params={"size":100,"page":num},headers=constants.media).json()["medias"]
            count = len(z)
        return True


    def getJournal(self):
        """
        Downloads the journal posts from the user
        :params: none
        :return: none
        """
        self.getJournalList()
        self.progbarj = tqdm(total=self.totalj, desc='Downloading journal posts of %s'%self.username, unit=' posts')    
        for x in self.works:
            path = os.path.join(os.getcwd(), x[0])
            if not os.path.exists(path):
                os.makedirs(path)
            os.chdir(path)
            x.pop(0)
            with ThreadPoolExecutor(max_workers=5) as executor:
                future_to_url = {executor.submit(self.download_img_journal,part):part for part in x}
                for future in concurrent.futures.as_completed(future_to_url):
                    part = future_to_url[future]
                    try:
                        data=future.result()
                    except Exception as exc:
                        print('%r crashed %s' % (part,exc))
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
        self.jour_found = self.session.get(self.journalurl,params={"size":10000,"page":1},headers=constants.media).json()["articles"]
        self.pbarjlist = tqdm(desc='Finding new journal posts of %s' %self.username, unit=' posts')
        for x in self.jour_found:
            self.works.append([x["permalink"]])
        path = os.path.join(os.getcwd(), "journal")
        if not os.path.exists(path):
            os.makedirs(path)
        os.chdir(path)
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_url = {executor.submit(self.makeListJournal, len(self.jour_found), val): val for val in range(len(self.jour_found))}
            for future in concurrent.futures.as_completed(future_to_url):
                val = future_to_url[future]
                try:
                    data=future.result()
                except Exception as exc:
                   print('%r crashed %s' % (val,exc))
        self.pbarjlist.close()

    def makeListJournal(self, num, loc):
        """
        Makes the list of all journal entries on the users page
        :params: num, loc
        :return: a boolean on whether the journal media was able to be grabbed
        """
        for item in self.jour_found[loc]["body"]:
            if item['type'] == "image":
                if os.path.exists(os.path.join(os.getcwd(),self.jour_found[loc]["permalink"])):
                    if '%s.jpg' % str(item["content"][0]["id"]) in os.listdir(os.path.join(os.getcwd(),self.jour_found[loc]["permalink"])):
                        continue
                self.works[loc].append(["http://%s"% item["content"][0]["responsive_url"],item["content"][0]["id"],"img"])
            elif item['type'] == "video":
                if os.path.exists(os.path.join(os.getcwd(),self.jour_found[loc]["permalink"])):
                    if '%s.mp4' % str(item["content"][0]["id"])in os.listdir(os.path.join(os.getcwd(),self.jour_found[loc]["permalink"])):
                        continue
                self.works[loc].append(["http://%s"% item["content"][0]["video_url"],item["content"][0]["id"],"vid"])
            elif item['type'] == "text":
                if os.path.exists(os.path.join(os.getcwd(),self.jour_found[loc]["permalink"])):
                    if '%s.txt' % str(item["content"]) in os.listdir(os.path.join(os.getcwd(),self.jour_found[loc]["permalink"])):
                        continue
                self.works[loc].append([item["content"],"txt"])
            self.totalj +=1
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
            with open("%s.txt"%str(lists[0]),'w') as f:
                f.write(lists[0])
        if lists[2] == "img":
            if '%s.jpg' % lists[1] in os.listdir():
                return True
            with open('%s.jpg'%str(lists[1]),'wb') as f:
                f.write(requests.get(lists[0] ,stream=True).content)
            
        elif lists[2] == "vid":
            if '%s.mp4' % lists[1] in os.listdir():
                return True
            with open('%s.mp4'%str(lists[1]),'wb') as f:
                for chunk in requests.get(lists[0] ,stream=True).iter_content(chunk_size=1024): 
                    if chunk:
                        f.write(chunk)
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
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_url = {executor.submit(self.download_img_normal,lists): lists for lists in self.imagelist}
            for future in tqdm(concurrent.futures.as_completed(future_to_url), total=len(self.imagelist), desc='Downloading posts of %s'%self.username, unit=' posts'):
                liste = future_to_url[future]
                try:
                    data=future.result()
                except Exception as exc:
                    print('%r crashed %s' % (liste,exc))


    def getImageList(self):
        """
        tqdm is a great library isn't it

        :params: none
        :return: none
        """
        self.pbar = tqdm(desc='Finding new posts of %s' %self.username, unit=' posts')
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_url = {executor.submit(self.makeImageList,num): num for num in range(5)}
            for future in concurrent.futures.as_completed(future_to_url):
                num=future_to_url[future]
                try:
                    data=future.result()
                except Exception as exc:
                    print('%r crashed %s' % (num,exc))
        self.pbar.close()

    def makeImageList(self, num):
        """
        At this point I'm only doing these comments out of a general sense I should comment
        all these functions after that one PR did it

        Don't ask me how it works, frankly I'm surprised it does
        
        :params: num - I remember looking at this after starting to merge the prs and wondering why I did num += 5. Still couldn't tell you. 
        :return: a boolean on whether the journal media was able to be grabbed
        """
        num +=1
        z = self.session.get(self.mediaurl,params={"size":100,"page":num},headers=constants.media).json()["media"]
        count = len(z)
        while count>0:
            for url in z:
                if '%s.jpg' % str(url["upload_date"])[:-3] in os.listdir() or '%s.mp4' % str(url["upload_date"])[:-3] in os.listdir():
                    continue
                if url['is_video'] is True:
                    self.imagelist.append(["http://%s"% url["video_url"],str(url["upload_date"])[:-3],True])
                    self.pbar.update()
                else:
                    self.imagelist.append(["http://%s"% url["responsive_url"],str(url["upload_date"])[:-3],False])
                    self.pbar.update()
            num +=5
            z = self.session.get(self.mediaurl,params={"size":100,"page":num},headers=constants.media).json()["media"]
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
            if '%s.jpg' % lists[1] in os.listdir():
                return True
            with open('%s.jpg'%str(lists[1]),'wb') as f:
                f.write(requests.get(lists[0] ,stream=True).content)
        else:
            if '%s.mp4' % lists[1] in os.listdir():
                return True
            with open('%s.mp4'%str(lists[1]),'wb') as f:
                for chunk in requests.get(lists[0] ,stream=True).iter_content(chunk_size=1024): 
                    if chunk:
                        f.write(chunk)
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

def parser():
    """Returns the parser arguments
    :params: none
    :return: parser.parse_args() object
    """
    parser = argparse.ArgumentParser(
    description="Scrapes a specified users VSCO Account")
    parser.add_argument('username', type=str, help='VSCO user to scrape or file name to read usernames off of. Filename feature works with -m, -mc, -mj, and -a only')
    parser.add_argument('-s', '--siteId', action="store_true", help='Grabs VSCO siteID for user')
    parser.add_argument('-i', '--getImages', action="store_true", help='Get the pictures of the user')
    parser.add_argument('-j', '--getJournal', action="store_true", help='Get the journal images of the user')
    parser.add_argument('-c','--getCollection',action="store_true", help='Get the collection images of the user')
    parser.add_argument('-m', '--multiple',action="store_true", help='Scrape multiple users')
    parser.add_argument('-mj','--multipleJournal',action="store_true", help='Scrape multiple users journal')
    parser.add_argument('-mc','--multipleCollection',action="store_true", help='Scrape multiple users collection')
    parser.add_argument('-a', '--all', action="store_true", help='Scrape multiple users journals and images')
    return parser.parse_args()
            
def main():
    args = parser()

    if args.siteId:
        scraper = Scraper(args.username)
        print(scraper.newSiteId())

    if args.getImages:
        scraper = Scraper(args.username)
        scraper.getImages()

    if args.getJournal:
        scraper = Scraper(args.username)
        scraper.getJournal()

    if args.getCollection:
        scraper = Scraper(args.username)
        scraper.getCollection()

    if args.multiple:
        y = []
        vsco = os.getcwd()
        with open(args.username,'r') as f:
            for x in f:
                y.append(x.replace("\n", ""))
        for z in y:
            try:
                os.chdir(vsco)
                Scraper(z).getImages()
                print()
            except:
                print("%s crashed" % z)
                pass

    if args.multipleJournal:
        y = []
        vsco = os.getcwd()
        with open(args.username,'r') as f:
            for x in f:
                y.append(x.replace("\n", ""))
        for z in y:
            try:
                os.chdir(vsco)
                Scraper(z).getJournal()
                print()
            except:
                print("%s crashed" % z)
                pass

    if args.multipleCollection:
        y = []
        vsco = os.getcwd()
        with open(args.username,'r') as f:
            for x in f:
                y.append(x.replace("\n", ""))
        for z in y:
            try:
                os.chdir(vsco)
                Scraper(z).getCollection()
                print()
            except:
                print("%s crashed" % z)
                pass

    if args.all:
        y = []
        vsco = os.getcwd()
        with open(args.username,'r') as f:
            for x in f:
                y.append(x.replace("\n", ""))
        for z in y:
            try:
                os.chdir(vsco)
                Scraper(z).run_all()
                print()
            except:
                print("%s crashed" % z)
                pass
    
if __name__ == '__main__':
    main()
