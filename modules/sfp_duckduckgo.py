# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------------
# Name:         sfp_duckduckgo
# Purpose:      Queries DuckDuckGo's API for information abotut the target.
#
# Author:      Steve Micallef <steve@binarypool.com>
#
# Created:     21/07/2015
# Copyright:   (c) Steve Micallef 2015
# Licence:     GPL
# -------------------------------------------------------------------------------

import json
from sflib import SpiderFoot, SpiderFootPlugin, SpiderFootEvent

class sfp_duckduckgo(SpiderFootPlugin):
    """DuckDuckGo:Footprint,Investigate,Passive:Search Engines::Query DuckDuckGo's API for descriptive information about your target."""

    meta = {
		'name': "DuckDuckGo",
		'summary': "Query DuckDuckGo's API for descriptive information about your target.",
		'flags': [ "" ],
		'useCases': [ "Footprint", "Investigate", "Passive" ],
		'categories': [ "Search Engines" ],
        'dataSource': {
            'website': "https://duckduckgo.com/",
            'model': "FREE_NOAUTH_UNLIMITED",
            'references': [
                "https://api.duckduckgo.com/api",
                "https://help.duckduckgo.com/company/partnerships/",
                "https://help.duckduckgo.com/duckduckgo-help-pages/"
            ],
            'favIcon': "https://duckduckgo.com/favicon.ico",
            'logo': "https://duckduckgo.com/assets/icons/meta/DDG-icon_256x256.png",
            'description': "Our Instant Answer API gives you free access to many of our instant answers like: "
                                "topic summaries , categories, disambiguation, and !bang redirects.\n",
        }
	}

    # Default options
    opts = {
            "affiliatedomains": True
    }

    # Option descriptions
    optdescs = {
            "affiliatedomains": "For affiliates, look up the domain name, not the hostname. This will usually return more meaningful information about the affiliate."
    }

    results = None

    def setup(self, sfc, userOpts=dict()):
        self.sf = sfc
        self.results = self.tempStorage()

        for opt in list(userOpts.keys()):
            self.opts[opt] = userOpts[opt]

    # What events is this module interested in for input
    def watchedEvents(self):
        return ["DOMAIN_NAME", "DOMAIN_NAME_PARENT",
                "INTERNET_NAME", "AFFILIATE_INTERNET_NAME"]

    # What events this module produces
    # This is to support the end user in selecting modules based on events
    # produced.
    def producedEvents(self):
        return ["DESCRIPTION_CATEGORY", "DESCRIPTION_ABSTRACT",
                "AFFILIATE_DESCRIPTION_CATEGORY",
                "AFFILIATE_DESCRIPTION_ABSTRACT"]


    def handleEvent(self, event):
        eventName = event.eventType
        srcModuleName = event.module
        eventData = event.data

        if self.opts['affiliatedomains'] and "AFFILIATE_" in eventName:
            eventData = self.sf.hostDomain(eventData, self.opts['_internettlds'])
            if not eventData:
                return None

        if eventData in self.results:
            self.sf.debug("Already did a search for " + eventData + ", skipping.")
            return None
        else:
            self.results[eventData] = True

        url = "https://api.duckduckgo.com/?q=" + eventData + "&format=json&pretty=1"
        res = self.sf.fetchUrl(url, timeout=self.opts['_fetchtimeout'],
                               useragent="SpiderFoot")

        if res['content'] == None:
            self.sf.error("Unable to fetch " + url, False)
            return None

        try:
            ret = json.loads(res['content'])
        except BaseException as e:
            return None

        if ret['Heading'] == "":
            self.sf.debug("No DuckDuckGo information for " + eventData)
            return None

        # Submit the bing results for analysis
        evt = SpiderFootEvent("SEARCH_ENGINE_WEB_CONTENT", res['content'],
                              self.__name__, event)
        self.notifyListeners(evt)

        if 'AbstractText' in ret:
            name = "DESCRIPTION_ABSTRACT"
            if "AFFILIATE" in eventName:
                name = "AFFILIATE_" + name

            evt = SpiderFootEvent(name, ret['AbstractText'],
                                  self.__name__, event)
            self.notifyListeners(evt)

        if 'RelatedTopics' in ret:
            name = "DESCRIPTION_CATEGORY"
            if "AFFILIATE" in eventName:
                name = "AFFILIATE_" + name

            for item in ret['RelatedTopics']:
                cat = None
                if 'Text' in item:
                    cat = item['Text']
                if cat == None or cat == "":
                    self.sf.debug("No category text found from DuckDuckGo.")
                    continue

                evt = SpiderFootEvent(name, cat, self.__name__, event)
                self.notifyListeners(evt)

# End of sfp_duckduckgo class
