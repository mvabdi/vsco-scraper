import argparse
from tqdm import tqdm
import requests
import constants
from bs4 import BeautifulSoup as bs
import time
import random
import os
import geocoder
import gmplot
import datetime
from pytz import timezone

class Scraper(object):

    def __init__(self, username):
      self.username = username
      self.session = requests.Session() 
      self.session.get("http://vsco.co/content/Static/userinfo?callback=jsonp_%s_0"% (str(round(time.time()*1000))),headers=constants.visituserinfo)
      self.uid = self.session.cookies.get_dict()['vs']
      path = "%s\%s"% (os.getcwd(),self.username)
      if not os.path.exists(path):
          os.makedirs(path)
      os.chdir(path)
      self.newSiteId()
      self.buildJSON()

    def newSiteId(self):
        base = "http://vsco.co/"
        res = self.session.get("http://vsco.co/ajxp/%s/2.0/sites?subdomain=%s" % (self.uid,self.username))
        self.siteid = res.json()["sites"][0]["id"]
        return self.siteid

    def buildJSON(self):
        self.mediaurl = "http://vsco.co/ajxp/%s/2.0/medias?site_id=%s" % (self.uid,self.siteid)
        self.journalurl = "http://vsco.co/ajxp/%s/2.0/articles?site_id=%s" % (self.uid,self.siteid)
        return self.mediaurl

    def makeJS(self):
        return """window.location.href='http://vsco.co';document.cookie = 'vs=%s; path=/; domain=.vsco.co';window.location.href='%s';""" %(self.uid,self.mediaurl)

    def makeJournalJS(self):
        return """window.location.href='http://vsco.co';document.cookie = 'vs=%s; path=/; domain=.vsco.co';window.location.href='%s';""" %(self.uid,self.journalurl)
        
    def getImages(self):
        page = 1
        r = self.session.get(self.mediaurl,headers=constants.media,params = {"page":"%s"%page})
        videos = []
        images = []
        videx = 0
        total = 0
        count = len(r.json()["media"])
        page = 1
        while count > 0:
            r = self.session.get(self.mediaurl,headers=constants.media,params = {"page":"%s"%page})
            page+=1                 
            count = len(r.json()["media"])
            total += count
        r = self.session.get(self.mediaurl,headers=constants.media,params = {"size":"%s"%total})
        red = r.json()["media"]
        for vid in tqdm(red,total=total):
            if vid['is_video'] is True:
                if '%s.mp4' % str(vid["upload_date"])[:-3] in os.listdir():
                    videx +=1
                    continue
                videx +=1
                vid_indiv = "http://%s"% vid["video_url"]
                videos.append(vid_indiv)
                with open('%s.mp4'%str(vid["upload_date"])[:-3],'wb') as f:
                    for chunk in requests.get(vid_indiv ,stream=True).iter_content(chunk_size=1024): 
                        if chunk:
                            f.write(chunk)
            if vid['is_video'] is False:
                if '%s.jpg' % str(vid["upload_date"])[:-3] in os.listdir():
                    videx +=1
                    continue
                videx += 1
                img_indiv = "http://%s"% vid["responsive_url"]
                images.append(img_indiv)
                with open('%s.jpg'%str(vid["upload_date"])[:-3],'wb') as f:
                    f.write(requests.get(img_indiv ,stream=True).content)
        print("Videos and Images of %s downloaded"%self.username)


    def plotter(self):
        page=1
        r = self.session.get(self.mediaurl,headers=constants.media,params = {"page":"%s"%page}) 
        count = len(r.json()["media"])
        coords = []
        index = 0
        indexs = []
        while count > 0:
            for loc in r.json()["media"]:
                if loc["has_location"]:
                    coords.append([loc["location_coords"][1],loc["location_coords"][0],datetime.datetime.fromtimestamp(int(loc["capture_date"])/1000).strftime('%Y-%m-%d %I:%M:%S %p')])
                    index +=1
                    indexs.append(index)
                else:
                    index+=1
                    continue
            page+=1                 
            r = self.session.get(self.mediaurl,headers=constants.media,params = {"page":"%s"%page})
            count = len(r.json()["media"])
        gmap = gmplot.GoogleMapPlotter(39.106506,-77.555574,13)
        gmap.coloricon = 'file:///' + os.path.dirname(gmplot.__file__).replace('\\', '/') + '/markers/%s.png'
        index = 0
        for coord in tqdm(coords,total=len(coords)):
            index +=1
            g = geocoder.google([coord[0],coord[1]],method='reverse').address
            crindex = 0
            while g is None:
                g = geocoder.google([coord[0],coord[1]],method='reverse').address
                crindex +=1
                if crindex == 10:
                    break
                else:
                    time.sleep(.3)
            gmap.marker(coord[0],coord[1], '#3B0B39','#E0FFFF', title="%s at %s" %(g,coord[2]))
            time.sleep(.15)
        gmap.draw("markers.html")
        return gmap        
    def getJournal(self):
        page = 1
        r = self.session.get(self.journalurl,headers=constants.media,params = {"page":"%s"%page})
        count = len(r.json()["articles"])
        videx = 0
        total = 0
        while count > 0:    
            r = self.session.get(self.journalurl,headers=constants.media,params = {"page":"%s"%page})
            page+=1                 
            for x in r.json()["articles"]:
                total += len(x["body"])  
            count = len(r.json()["articles"])   
        path = "%s\journal" % (os.getcwd())
        if not os.path.exists(path):
            os.makedirs(path)
        os.chdir(path)
        pbar = tqdm(total=total)
        r = self.session.get(self.journalurl,headers=constants.media,params = {"size":"%s"%total}) 
        for j in r.json()["articles"]:
            path = "%s\%s"% (os.getcwd(),str(j["permalink"]))
            if not os.path.exists(path):
                os.makedirs(path)
            os.chdir(path)
            for img in j["body"]:
                if img["type"] == "video":
                    if '%s.mp4' % img["content"][0]["id"] in os.listdir():
                        videx +=1
                        pbar.update(1)
                        continue
                    videx +=1            
                    vid_indiv = "http://%s"% img["content"][0]["responsive_url"]
                    pbar.update(1)
                    with open('%s.mp4'%img["content"][0]["id"],'wb') as f:
                        for chunk in requests.get(vid_indiv ,stream=True).iter_content(chunk_size=1024): 
                            if chunk:                         
                                f.write(chunk)
                if img["type"] == "image":
                    if '%s.jpg' % img["content"][0]["id"] in os.listdir():
                        videx +=1
                        pbar.update(1)
                        continue
                    videx += 1
                    img_indiv = "http://%s"% img["content"][0]["responsive_url"]
                    pbar.update(1)
                    with open('%s.jpg'%img["content"][0]["id"],'wb') as f:
                        f.write(requests.get(img_indiv ,stream=True).content)       
            os.chdir(os.path.normpath(os.getcwd() + os.sep + os.pardir))
        pbar.close()

                

def main():
    parser = argparse.ArgumentParser(
    description="Scrapes a specified users VSCO, currently only supports one user at a time")
    parser.add_argument('username', help='VSCO user to scrape')
    parser.add_argument('-s','--siteId',action="store_true", help='Grabs VSCO siteID for user')
    parser.add_argument('-p','--plot',action="store_true", help='Plots locations of pictures on the VSCO')
    parser.add_argument('-i','--getImages',action="store_true", help='Get the pictures of the user')
    parser.add_argument('-j','--getJournal',action="store_true", help='Get the Journal of the user')
    args = parser.parse_args()

    
    scraper = Scraper(args.username)

    if args.siteId:
        print(scraper.newSiteId())

    if args.getImages:
        scraper.getImages()

    if args.getJournal:
        scraper.getJournal()

    if args.plot:
        scraper.plotter()

    



if __name__ == '__main__':
    main()

        
    







    
