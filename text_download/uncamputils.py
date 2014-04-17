# Copyright 2013 The Trustees of Indiana University
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either expressed or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

'''
Created on Aug 23, 2013

This util file provides the method to obtain OAuth2 token from authentication server and the method 
to wrtie a zip stream to a zip file. It also includes service endpoint constants and url suffix for
Data API request 
'''

import urllib
import urllib2
import json
import zipfile

##########################################################################
#        Default Data API/Solr/OAuth2 setting (No need to change)        #
##########################################################################
PAGE_URL_REQUEST = "/pages"
VOLUME_URL_REQUEST = "/volumes"
TOKENCOUNT_URL_REQUEST = "/tokencount"

OA2_EPR = "https://sandbox.htrc.illinois.edu:9443/oauth2endpoints/token?grant_type=client_credentials"
DATAAPI_EPR = "https://sandbox.htrc.illinois.edu:25443/data-api"
SOLR_METADATA_URL = "http://sandbox.htrc.illinois.edu:9994/solr/meta/select?"
SOLR_OCR_URL = "http://sandbox.htrc.illinois.edu:9994/solr/ocr/select?q=ocr:"

# OA2_EPR = "https://silvermaple.pti.indiana.edu:9443/oauth2endpoints/token?grant_type=client_credentials"
# DATAAPI_EPR = "https://silvermaple.pti.indiana.edu:25443/data-api"
# SOLR_METADATA_URL = "http://sandbox.htrc.illinois.edu:9994/solr/meta/select?"
# SOLR_OCR_URL = "http://sandbox.htrc.illinois.edu:9994/solr/ocr/select?q=ocr:"

def obtainOAuth2Token(endpoint, clientID, clientSecret):
    """ function that authorizes with OAuth2 token endpoint, obtains and returns an OAuth2 token
    
    arguments:
    clientID -- client ID or username
    clientSecret -- client secret or password
    
    returns OAuth2 token upon successful authroization.
    raises exception if authorization fails
    """
    
    # content-type http header must be "application/x-www-form-urlencoded"
    headers = {'content-type' : 'application/x-www-form-urlencoded'}
     
    # request body
    values = {'grant_type' : 'client_credentials',
          'client_id' : clientID,
          'client_secret' : clientSecret }
    body = urllib.urlencode(values)
     
    # request method must be POST
    req = urllib2.Request(endpoint, body, headers)
    try:
        # urllib2 module sends HTTP/1.1 requests with Connection:close header included
        response = urllib2.urlopen(req)
         
        # any other response code means the OAuth2 authentication failed. raise exception
        if (response.code != 200):
            raise urllib2.HTTPError(response.url, response.code, response.read(), response.info(), response.fp)
         
        # response body is a JSON string
        oauth2JsonStr = response.read()
         
        # parse JSON string using python built-in json lib
        oauth2Json = json.loads(oauth2JsonStr)
         
        # return the access token
        return oauth2Json["access_token"]
    
    # response code in the 400-599 range will raise HTTPError
    except urllib2.HTTPError as e:
        # just re-raise the exception
        raise Exception(str(e.code) + " " + str(e.reason) + " " + str(e.info) + " " + str(e.read())) 

def writeZipFile(zipcontent, zipfilepath):    
    """ function that writes text to a zip file
    
    arguments:
    zipcontent -- text returned from Data API
    zipfilepath -- zip file name to be written
    """
    
    # open file to write
    zf = zipfile.ZipFile(zipfilepath, mode='w')
    
    # read from zip stream
    zippedFile = zipfile.ZipFile(zipcontent, "r")
    try:
        # getting a list of entries in the ZIP
        infoList = zippedFile.infolist()
        for zipInfo in infoList:
            entryName = zipInfo.filename
            entry = zippedFile.open(entryName, "r")
            
            # read zip entry content 
            content = ''
            line = entry.readline()
            while (line != ""):
                line = entry.readline()
                content += line
            
            # remember to close each entry
            entry.close()
            
            # write to zip file in disk
            zf.writestr(zipInfo, content)
        
    finally:
        print 'Closing zip file'
        zf.close()
        zippedFile.close()


def appendToZipFile(zipcontent, zf):    
    """ function that writes text to a zip file
    
    arguments:
    zipcontent -- text returned from Data API
    zf -- zip file to be appended
    """
    
    # read from zip stream
    zippedFile = zipfile.ZipFile(zipcontent, "r")
    
    try:
        # getting a list of entries in the ZIP
        infoList = zippedFile.infolist()
        for zipInfo in infoList:
            entryName = zipInfo.filename
            entry = zippedFile.open(entryName, "r")
            
            # read zip entry content 
            content = ''
            line = entry.readline()
            while (line != ""):
                line = entry.readline()
                content += line
            
            # remember to close each entry
            entry.close()
            
            # write to zip file in disk
            zf.writestr(zipInfo, content)
    finally:
        zippedFile.close()
       
