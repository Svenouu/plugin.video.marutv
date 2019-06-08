# -*- coding: utf-8 -*-
"""
    MaruTV - Korea Drama/TV Shows Streaming Service
"""

import xbmcgui
import urllib2
import urlparse
import re
import requests
import json
from bs4 import BeautifulSoup
import resolveurl

ROOT_URL = ''
ROOT_URL_TV = ''
UserAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36"

def parseProgList(main_url):
    req = urllib2.Request(main_url)
    req.add_header('User-Agent', UserAgent)
    req.add_header('Referer', 'http://www.marutv.org/')
    resp = urllib2.urlopen(req)
    doc = resp.read()
    resp.close()
    soup = BeautifulSoup(doc, from_encoding='utf-8')

    result = {'link':[]}
    for item in soup.findAll("div", {"class":"item-img"}):
        thumb = ""
        if item.a.img:
            thumb = item.a.img['src']
        h3item = item.find_next('h3')
        if h3item:
            title = h3item.text.replace('&amp;','&')
            title,date = re.compile('(.* )\s*(\d+/\d+/\d+)').search(title).group(1,2)
            if date:
                title = date + " " + title
            url = item.a['href']
            token = url.split('/')
            id = token[-2]
            result['link'].append({'title':title, 'cate':'video', 'id':id, 'thumbnail':thumb})

    # navigation
    cur = soup.find("ul", {"class":"pagination"}).find("span", {"class":"current"}).parent
    p = cur.findPreviousSibling("li")
    if p and p.a and p.a.text.isdigit():
        url = p.a['href']
        result['prevpage'] = url
    p = cur.findNextSibling("li")
    if p and p.a and p.a.text.isdigit():
        url = p.a['href']
        result['nextpage'] = url
    return result

def parseSearchList(main_url):
    req = urllib2.Request(main_url)
    req.add_header('User-Agent', UserAgent)
    req.add_header('Referer', 'http://www.marutv.org/')
    resp = urllib2.urlopen(req)
    doc = resp.read()
    resp.close()
    soup = BeautifulSoup(doc, from_encoding='utf-8')

    result = {'link':[]}
    for item in soup.findAll("div", {"class":"item"}):
        thumb = ""
        if item.a.img:
            thumb = item.a.img['src']
        h3item = item.find_next('h3')
        if h3item:
            if h3item.a:
                title = h3item.a.text.replace('&amp;','&')
                title,date = re.compile('(.* )\s*(\d+/\d+/\d+)').search(title).group(1,2)
                if date:
                    title = date + " " + title
                url = item.a['href']
                token = url.split('/')
                id = token[-2]
                result['link'].append({'title':title, 'cate':'video', 'id':id, 'thumbnail':thumb})

    # navigation
    cur = soup.find("ul", {"class":"pagination"}).find("span", {"class":"current"}).parent
    p = cur.findPreviousSibling("li")
    if p and p.a and p.a.text.isdigit():
        url = p.a['href']
        result['prevpage'] = url
    p = cur.findNextSibling("li")
    if p and p.a and p.a.text.isdigit():
        url = p.a['href']
        result['nextpage'] = url
    return result

def parseVideoList(main_url):
    req = urllib2.Request(main_url)
    req.add_header('User-Agent', UserAgent)
    req.add_header('Referer', 'http://www.marutv.org/')
    resp = urllib2.urlopen(req)
    doc = resp.read()
    resp.close()
    soup = BeautifulSoup(doc, from_encoding='utf-8')
    result = []
    #web_pdb.set_trace()
    pagination = soup.find("ul", {"class":"pagination"})

    if pagination:
        for item in pagination.findAll('a'):
            url = item['href']
            if url.endswith('?tape=1'):
                url.replace('?tape=1','')
            if url.startswith('//'):
                url = "http:" + url
            elif not url.startswith('http://'):
                url = ROOT_URL + url
            title = item.text
            result.append({'title':title, 'url':url, 'decoded':False})
    else:
        player = soup.find("div", {"class":"player"})
        iframe = player.find('iframe')
        if iframe:
            result.append({'title':'링크 1', 'url':main_url, 'decoded':False})

    return result

def extract_video_url(url):
    vid_url = None

    req = urllib2.Request(url)
    req.add_header('User-Agent', UserAgent)
    req.add_header('Referer', 'http://www.marutv.org/')
    resp = urllib2.urlopen(req)
    doc = resp.read()
    resp.close()
    soup = BeautifulSoup(doc, from_encoding='utf-8')

    player = soup.find("div", {"class":"player"})

    vid_url = ''
    if player:
        iframe = player.find('iframe')
        if iframe:
            vid_url = iframe['src']
        else:
            btn = player.find('a')
            if btn:
                vid_url = btn['href']
    
    # normalize url
    soup = None
    
    resolved = resolveurl.resolve(vid_url)
    if not resolved:
        return tryresolveurl(vid_url)
    return resolved

def tryresolveurl(vid_url):
    if 'k-vid.net' in vid_url or 'dramacool9' in vid_url:
        return resolveurl_kvid(vid_url)
    elif 'verystream' in vid_url:
        return resolveurl_verystream(vid_url)
    elif 'xstreamcdn.com' in vid_url:
        return resolveurl_xstreamcdn(vid_url)
    elif 'toctube.space' in vid_url:
        return resolveurl_peertube(vid_url, 'toctube.space')
    elif 'toctube.club' in vid_url:
        return resolveurl_peertube(vid_url, 'toctube.club')
    else:
        ips = re.findall( r'[0-9]+(?:\.[0-9]+){3}', vid_url )
        if ips:
            return resolveurl_peertube(vid_url, ips[0])
            
    return vid_url

def resolveurl_peertube(vid_url, ip):
    uuid = vid_url.split('/')[-1]
    current_res = 0
    higher_res = -1
    file_url = ''
    resp = urllib2.urlopen('http://'+ ip +'/api/v1/videos/' + uuid)
    metadata = json.load(resp)
    
    for f in metadata['files']:
        # Get file resolution
        res = f['resolution']['id']
        if res > current_res:
            file_url = f['fileUrl'] 
            current_res = res
        elif ( res < higher_res or higher_res == -1 ):
            file_url = f['fileUrl'] 
            higher_res = res
    
    return file_url

def resolveurl_xstreamcdn(vid_url):
    req = urllib2.Request(vid_url)
    req.add_header('User-Agent', UserAgent)
    req.add_header('Referer', 'https://xstreamcdn.com/')
    resp = urllib2.urlopen(req)
    doc = resp.read()
    resp.close()
    soup = BeautifulSoup(doc, from_encoding='utf-8')
    video = soup.find("video")
    
    if video:
        return video['src']
    else:
        return vid_url

def resolveurl_verystream(vid_url):
    req = urllib2.Request(vid_url)
    req.add_header('User-Agent', UserAgent)
    req.add_header('Referer', 'https://verystream.com/')
    resp = urllib2.urlopen(req)
    doc = resp.read()
    resp.close()
    soup = BeautifulSoup(doc, from_encoding='utf-8')
    videolink = soup.find(id="videolink")
    if videolink:
        return "https://verystream.com/gettoken/" + videolink.text
    else:
        return vid_url

def resolveurl_kvid(vid_url):
    req = urllib2.Request(vid_url)
    req.add_header('User-Agent', UserAgent)
    req.add_header('Referer', 'http://www.marutv.org/')
    resp = urllib2.urlopen(req)
    doc = resp.read()
    resp.close()
    soup = BeautifulSoup(doc, from_encoding='utf-8')
    embedVids = soup.findAll("li", {"class":"linkserver"})

    soup = None
    if embedVids:
        urlsFound = {}
        for embedVid in embedVids:
            datavideo = embedVid['data-video'] 
            if datavideo:
                urlsFound[embedVid.text] = datavideo
        if urlsFound:
            dialog = xbmcgui.Dialog()
            ret = dialog.select('Choose source', urlsFound.keys())
            if ret >= 0:
                resolved = resolveurl.resolve(urlsFound.values()[ret])
                if resolved:
                    return resolved
                else:
                    return tryresolveurl(urlsFound.values()[ret])
    return vid_url
if __name__ == "__main__":
    pass

# vim:sts=4:sw=4:et
