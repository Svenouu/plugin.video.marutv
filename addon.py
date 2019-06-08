# -*- coding: utf-8 -*-
"""
    MaruTV
"""
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
from xbmcgui import ListItem
from xbmcplugin import addDirectoryItem, endOfDirectory
from xbmcswift2 import Plugin
import urllib
import sys
import os
import re
from YDStreamExtractor import getVideoInfo

addon = xbmcaddon.Addon()
plugin = Plugin()
_L = plugin.get_string

plugin_path = addon.getAddonInfo('path')
url_root = addon.getSetting('root_url')
url_root_tv = addon.getSetting('root_urltv')
lib_path = os.path.join(plugin_path, 'resources', 'lib')
sys.path.append(lib_path)

import marutv

tPrevPage = u"[B]<%s[/B]" % _L(30100)
tNextPage = u"[B]%s>[/B]" % _L(30101)

@plugin.route('/')
def main_menu():
    items = [
        {'label':u"Search", 'path':plugin.url_for('search_list', searchTerms='-', page='-')},
        {'label':u"Drama", 'path':plugin.url_for("prog_list", cate='drama', page='-')},        
        {'label':u"Entertainment", 'path':plugin.url_for("prog_list", cate='entertainment', page='-')},
        {'label':u"Documentary", 'path':plugin.url_for("prog_list", cate='current', page='-')},
        {'label':u"News", 'path':plugin.url_for("prog_list", cate='news', page='-')},
        {'label':u"Completed Drama", 'path':plugin.url_for("prog_list", cate='fin', page='-')}        
    ]
    return items

@plugin.route('/search/<searchTerms>/<page>/')
def search_list(searchTerms, page):
    marutv.ROOT_URL = url_root
    if searchTerms == '-':
        keyboard = xbmc.Keyboard()
        keyboard.doModal()
        if (keyboard.isConfirmed()):
            search_list(keyboard.getText(), '-')
    else:
        if page == '-' :
            pageN = 1 
        else:
            pageN = int(page)

        url = marutv.ROOT_URL+'page/%d/?s=%s&order_post=latest' % (pageN, searchTerms)

        result = marutv.parseSearchList(url)
        createVideoDirectory(result, searchTerms, pageN, True)
    return main_menu()


@plugin.route('/category/<cate>/<page>/')
def prog_list(cate, page):
    marutv.ROOT_URL = url_root

    if page == '-' :
        pageN = 1 
    else:
        pageN = int(page)
    
    if pageN == 1 :
        url = marutv.ROOT_URL+'%s/' % (cate)
    else:
        url = marutv.ROOT_URL+'%s/page/%d/' % (cate, pageN)

    result = marutv.parseProgList(url)
    
    createVideoDirectory(result, cate, pageN, False)

def createVideoDirectory(result, cateOrSearchTerms, pageN, isSearch):
    listing = []
    for video in result['link']:
        list_item = xbmcgui.ListItem(label=video['title'], thumbnailImage=video['thumbnail'])
        list_item.setInfo('video', {'title': video['title']})
        url = plugin.url_for('video_list', eid=video['id'])
        is_folder = True
        listing.append((url, list_item, is_folder))
    
    xbmcplugin.addDirectoryItems(plugin.handle, listing, len(listing))
    
    if 'prevpage' in result:
        if isSearch:
            addDirectoryItem(
                plugin.handle,
                plugin.url_for('search_list', searchTerms=cateOrSearchTerms, page=pageN-1),
                ListItem(tPrevPage), True)
        else:
            addDirectoryItem(
                plugin.handle,
                plugin.url_for('prog_list', cate=cateOrSearchTerms, page=pageN-1),
                ListItem(tPrevPage), True)
    if 'nextpage' in result:
        if isSearch:
            addDirectoryItem(
                plugin.handle,
                plugin.url_for('search_list', searchTerms=cateOrSearchTerms, page=pageN+1),
                ListItem(tNextPage), True)
        else:
            addDirectoryItem(
                plugin.handle,
                plugin.url_for('prog_list', cate=cateOrSearchTerms, page=pageN+1),
                ListItem(tNextPage), True)

    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route('/episode/<eid>/')
def video_list(eid):
    url = url_root+'video/'+eid+'/'
    info = marutv.parseVideoList(url)

    items = []
    prev_vurl = ""
    for item in info:
        vurl = item['url']
        if vurl != prev_vurl:
            items.append({'label':item['title'], 'path':plugin.url_for('play_video', url=vurl)})
            prev_vurl = vurl
    return items

@plugin.route('/play/<url>/')
def play_video(url):
    url = marutv.extract_video_url(url)
    info = None
    
    if not url.startswith("plugin://"):
        quality = plugin.get_setting('qualityPref', int)
        info = getVideoInfo(url, quality=quality, resolve_redirects=True)
    if info:
        streams = info.streams()
        plugin.log.debug("num of streams: %d" % len(streams))
        from xbmcswift2 import xbmc, xbmcgui
        pl = xbmc.PlayList( xbmc.PLAYLIST_VIDEO )
        pl.clear()
        for stream in streams:
            li = xbmcgui.ListItem(stream['title'], iconImage="DefaultVideo.png")
            li.setInfo( 'video', { "Title": stream['title'] } )
            pl.add(stream['xbmc_url'], li)
        xbmc.Player().play(pl)
    else:
        plugin.log.warning('Fallback to '+url)
        plugin.play_video({'path':url, 'is_playable':True})
    return plugin.finish(None, succeeded=False)     # trick not to enter directory mode

if __name__ == "__main__":
    plugin.run()

# vim:sw=4:sts=4:et
