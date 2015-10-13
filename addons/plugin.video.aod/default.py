#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import urlparse
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmc
import xbmcvfs
import urllib, urllib2, socket, cookielib, re, os, shutil,json

addon_handle = int(sys.argv[1])
addon = xbmcaddon.Addon()
translation = addon.getLocalizedString
icon = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('path')+'/icon.png').decode('utf-8')
global quality
quality=addon.getSetting("quality")
username=addon.getSetting("user")
password=addon.getSetting("pass")



profile    = xbmc.translatePath( addon.getAddonInfo('profile') ).decode("utf-8")
temp       = xbmc.translatePath( os.path.join( profile, 'temp', '') ).decode("utf-8")
if not xbmcvfs.exists(temp):  
  xbmcvfs.mkdirs(temp)




def debug(content):
    log(content, xbmc.LOGDEBUG)
    
def notice(content):
    log(content, xbmc.LOGNOTICE)

def log(msg, level=xbmc.LOGNOTICE):
    addon = xbmcaddon.Addon()
    addonID = addon.getAddonInfo('id')
    xbmc.log('%s: %s' % (addonID, msg), level) 

    
cookie=temp+"/cookie.jar"
cj = cookielib.LWPCookieJar();


if xbmcvfs.exists(cookie):
   cj.load(cookie,ignore_discard=True, ignore_expires=True)


opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
baseurl="https://www.anime-on-demand.de"
    
    
    
    
def ersetze(inhalt):
   inhalt=inhalt.replace('&#39;','\'')  
   inhalt=inhalt.replace('&quot;','"')    
   inhalt=inhalt.replace('&gt;','>')      
   inhalt=inhalt.replace('&amp;','&') 
   return inhalt

def addDir(name, url, mode, iconimage, desc=""):
	u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
	ok = True
	liz = xbmcgui.ListItem(name, iconImage=icon, thumbnailImage=iconimage)
	liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc})			
	ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
	return ok   
  
  
def addLink(name, url, mode, iconimage, duration="", desc="", genre='',csrftoken=""):
  debug("addlink :" + url)  
  u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&csrftoken="+csrftoken
  ok = True
  liz = xbmcgui.ListItem(name, thumbnailImage=iconimage)
  liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc, "Genre": genre})
  liz.setProperty('IsPlayable', 'true')
  liz.addStreamInfo('video', { 'duration' : duration })
  liz.setProperty("fanart_image", iconimage)
  #liz.setProperty("fanart_image", defaultBackground)
  xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
  ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
  return ok
  
def all(url=""):
   debug ("###Start ALL" + url)   
   content=geturl(url)   
   kurz_inhalt = content[content.find('<div class="three-box-container">')+1:]
   kurz_inhalt = kurz_inhalt[:kurz_inhalt.find('<div class="l-contentcontainer l-navigationscontainer">')]
   spl=kurz_inhalt.split('<div class="three-box animebox">')
   for i in range(1,len(spl),1):
      entry=spl[i]
      if not "zum Film" in entry or movies=="true"    :  
        match=re.compile('<h3 class="animebox-title">([^<]+)</h3>', re.DOTALL).findall(entry)
        title=match[0]
        match=re.compile('<img src="([^"]+)"', re.DOTALL).findall(entry)
        img=baseurl+match[0]
        match=re.compile('<a href="([^"]+)">', re.DOTALL).findall(entry)
        link=baseurl+match[0]
        match=re.compile('<p class="animebox-shorttext">.+</p>', re.DOTALL).findall(entry)
        desc=match[0]
        addDir(name=ersetze(title), url=link, mode="Serie", iconimage=img, desc=desc)
   xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)
   
def login(url):
    global opener
    global cj
    global username
    global password
    opener.addheaders = [('User-Agent', userAgent)]
    content=opener.open(baseurl+"/users/sign_in").read()
    match = re.compile('ame="authenticity_token" value="([^"]+)"', re.DOTALL).findall(content)
    token1=match[0]
    debug ("USERNAME: "+ username)
    values = {'user[login]' : username,
        'user[password]' : password,
        'user[remember_me]' : '1',
        'commit' : 'Einloggen' ,
        'authenticity_token' : token1
    }
    data = urllib.urlencode(values)
    content=opener.open(baseurl+"/users/sign_in",data).read()
    content=opener.open(url).read()
    return content
   
    
def Serie(url):
  global opener
  global cj
  global username
  global password
  
  userAgent = "Mozilla/5.0 (Windows NT 6.2; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0"
  opener.addheaders = [('User-Agent', userAgent)]
  content=opener.open(url).read()  
  if not '<a href="/users/edit">Benutzerkonto</a>' in content :    
    content=login(url)
  cj.save(cookie,ignore_discard=True, ignore_expires=True)
  match = re.compile('<meta name="csrf-token" content="([^"]+)"', re.DOTALL).findall(content)
  csrftoken=match[0]
  kurz_inhalt = content[content.find('<div class="three-box-container">')+1:]                                      
  kurz_inhalt = kurz_inhalt[:kurz_inhalt.find('<div class="l-contentcontainer l-navigationscontainer">')]
  spl=kurz_inhalt.split('<div class="three-box episodebox flip-container">')
  for i in range(1,len(spl),1):
    try:
      entry=spl[i]          
      match=re.compile('title="([^"]+)">', re.DOTALL).findall(entry)
      title=match[0]       
      match=re.compile('src="([^"]+)"', re.DOTALL).findall(entry)
      img=baseurl+match[0]
      match=re.compile('title="([^"]+)" data-stream="([^"]+)"', re.DOTALL).findall(entry)
      found=0      
      linka=""
      linko=""
      for qua,linka in match:        
        titl=quality+ "-Stream"         
        if titl.lower() in qua.lower():
            link=linka
            found=1
        else:
             linko=linka
      if found==0:         
         link=linko
      if link :
         link=baseurl+link
         debug("####### LINK # "+ link)      
         match=re.compile('<p class="episodebox-shorttext">.+</p>', re.DOTALL).findall(entry)
         desc=match[0]    
         desc=desc.replace('<p class="episodebox-shorttext">','')  
         desc=desc.replace("</p>",'')          
         addLink(name=ersetze(title), url=link, mode="Folge", iconimage=img, desc=desc,csrftoken=csrftoken)      
    except :
       error=1
  xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)  

def Folge(url,csrftoken):
  global opener
  global cj
  global username
  global password
        
  opener.addheaders = [('X-CSRF-Token', csrftoken),
                     ('X-Requested-With', "XMLHttpRequest"),
                     ('Accept', "application/json, text/javascript, */*; q=0.01")]
  content=opener.open(url).read()
  match = re.compile('"streamurl":"([^"]+)"', re.DOTALL).findall(content)
  stream=match[0]  
  match = re.compile('(.+)mp4:(.+)', re.DOTALL).findall(stream)  
  path="mp4:"+match[0][1]
  server=match[0][0]
  debug("SERVER: "+ server)
  debug("PATH: "+path)
  listitem = xbmcgui.ListItem (path=server +"swfUrl=https://ssl.p.jwpcdn.com/6/12/jwplayer.flash.swf playpath="+path+" token=83nqamH3#i3j app=aodrelaunch/ swfVfy=true")
  xbmcplugin.setResolvedUrl(addon_handle,True, listitem)    
  debug(content)

   
def geturl(url):   
   userAgent = "Mozilla/5.0 (Windows NT 6.2; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0"
   opener.addheaders = [('User-Agent', userAgent)]
   req = urllib2.Request(url)
   inhalt = urllib2.urlopen(req).read()   
   cj.save(cookie,ignore_discard=True, ignore_expires=True)
   return inhalt   
  
def parameters_string_to_dict(parameters):
	paramDict = {}
	if parameters:
		paramPairs = parameters[1:].split("&")
		for paramsPair in paramPairs:
			paramSplits = paramsPair.split('=')
			if (len(paramSplits)) == 2:
				paramDict[paramSplits[0]] = paramSplits[1]
	return paramDict


def category() :
  global opener
  global cj
  global username
  global password
  url=baseurl+"/animes"
  userAgent = "Mozilla/5.0 (Windows NT 6.2; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0"
  opener.addheaders = [('User-Agent', userAgent)]
  content=opener.open(url).read()  
  if not '<a href="/users/edit">Benutzerkonto</a>' in content :    
    content=login(url)
  cj.save(cookie,ignore_discard=True, ignore_expires=True)

  kurz_inhalt = content[content.find('<ul class="inline-block-list" style="display: block; text-align: center;">')+1:]                                      
  kurz_inhalt = kurz_inhalt[:kurz_inhalt.find('</ul>')]
  match=re.compile('<a href="([^"]+)">([^<]+)</a>', re.DOTALL).findall(kurz_inhalt)
  for link,name in match:
      addDir(name=ersetze(name), url=baseurl+link, mode="catall",iconimage="", desc="")
  xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)
 
def lanuage() :
  global opener
  global cj
  global username
  global password
  url=baseurl+"/animes"
  userAgent = "Mozilla/5.0 (Windows NT 6.2; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0"
  opener.addheaders = [('User-Agent', userAgent)]
  content=opener.open(url).read()  
  if not '<a href="/users/edit">Benutzerkonto</a>' in content :    
    content=login(url)
  cj.save(cookie,ignore_discard=True, ignore_expires=True)

  kurz_inhalt = content[content.find('<ul class="inline-block-list" style="display: block; text-align: center;">')+1:]     
  kurz_inhalt = kurz_inhalt[kurz_inhalt.find('<ul class="inline-block-list" style="display: block; text-align: center;">')+1:]                                      
  kurz_inhalt = kurz_inhalt[:kurz_inhalt.find('</ul>')]  
  match=re.compile('<a href="([^"]+)">([^<]+)</a>', re.DOTALL).findall(kurz_inhalt)
  for link,name in match:
      addDir(name=ersetze(name), url=baseurl+link, mode="catall",iconimage="", desc="")
  xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)
 
params = parameters_string_to_dict(sys.argv[2])  
mode = urllib.unquote_plus(params.get('mode', ''))
url = urllib.unquote_plus(params.get('url', ''))
csrftoken = urllib.unquote_plus(params.get('csrftoken', ''))
movies = urllib.unquote_plus(params.get('movies', ''))

def abisz():
  addDir("0-9", baseurl+"/animes/begins_with/0-9", 'catall', "")
  letters = [chr(i) for i in xrange(ord('a'), ord('z')+1)]
  for letter in letters:
		addDir(letter.upper(), baseurl+"/animes/begins_with/"+letter.upper(), 'catall', "")
  xbmcplugin.endOfDirectory(addon_handle)


if mode is '':
    addDir(translation(30104), translation(30104), 'AZ', "")
    addDir(translation(30105), translation(30105), 'cat', "")
    addDir(translation(30106), translation(30106), 'lang', "")    
    addDir(translation(30107), translation(30107), 'All', "") 
    addDir(translation(30108), translation(30108), 'Settings', "") 
    xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)
else:
  # Wenn Settings ausgewählt wurde
  if mode == 'Settings':
          addon.openSettings()
  # Wenn Kategory ausgewählt wurde
  if mode == 'All':
          all(baseurl+"/animes")
  if mode == 'Serie':
          Serie(url) 
  if mode == 'Folge':
          Folge(url,csrftoken)            
  if mode == 'cat':
          category()  
  if mode == 'lang':
          lanuage()  
  if mode == 'catall':
          all(url)
  if mode == 'AZ':
          abisz()
  if mode == 'getcontent_search':
          getcontent_search(url)             
