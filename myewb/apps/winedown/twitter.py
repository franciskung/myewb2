"""myEWB winedown twitter interface

This file is part of myEWB
Copyright 2011 Engineers Without Borders Canada
"""

import httplib, json, urllib
from datetime import datetime
from django.db.models import Max

from siteutils.helpers import to_ascii, fix_encoding
from siteutils.shortcuts import get_object_or_none
from winedown.models import Cheers, Tweet

import oauth2, settings

def load_tweets():
    since = Tweet.objects.all().aggregate(Max('twitter_id'))
    if since:
        since = since['twitter_id__max']

    #conn = httplib.HTTPConnection("search.twitter.com")
    #conn = httplib.HTTPConnection("api.twitter.com")

    consumer = oauth2.Consumer(key=settings.TWITTER_CONSUMER_KEY, secret=settings.TWITTER_CONSUMER_SECRET)
    token = oauth2.Token(key=settings.TWITTER_TOKEN_KEY, secret=settings.TWITTER_TOKEN_SECRET)
    conn = oauth2.Client(consumer, token)

    params = {'q': '@ewb OR #ewb OR from:ewb OR from:worldofewb'}  # add @ewb OR #ewb as query terms
    params['result_type'] = 'recent'        # want all recent tweets, not only popular ones...
    params['count'] = 100
    if since:
        params['since_id'] = since          # since is a tweet ID

    """
    #conn.request("GET", "/search.json?" + urllib.urlencode(params))
    conn.request("GET", "/1.1/search/tweets.json?" + urllib.urlencode(params))    
    response = conn.getresponse()
    print "status", response.status

    if response.status != 200:
        return False

    data = response.read()
    conn.close()

    print data
    """

    status, data = conn.request('https://api.twitter.com/1.1/search/tweets.json?' + urllib.urlencode(params), 'GET')
    if status['status'] != "200":
        return False

    result = json.loads(data)
    result['statuses'].reverse()
    
    for r in result['statuses']:
        tzdelta = datetime.now() - datetime.utcnow()
        parsed_date = datetime.strptime(r['created_at'], '%a %b %d %H:%M:%S +0000 %Y') + tzdelta
        
        tweet = None
        
        # retweet?  see what we can find...!
        text = r['text']
        if text[0:4] == 'RT @':
            try:
                original_tweeter = text.split(':')[0].split('@')[1].strip()
                original_tweet = text.split(':', 1)[1].strip()
            except IndexError:      # mis-formed retweets...?
                original_tweeter = text.split('@')[1].split(' ', 1)[0].strip()
                original_tweet = text.split('@')[1].split(' ', 1)[1].strip()
            
            tweet = get_object_or_none(Tweet, author_username=to_ascii(original_tweeter), text=to_ascii(original_tweet))
            
        if tweet:
            tweet.retweet(r)
        
        else:
            tweet, created = Tweet.objects.get_or_create(twitter_id=r['id_str'],
                                                         defaults={'text': r['text'],
                                                                   'author_name': r['user']['name'],
                                                                   'author_username': r['user']['screen_name'],
                                                                   'author_userid': r['user']['id'],
                                                                   'author_image': r['user']['profile_image_url'],
                                                                   'date': parsed_date})
            
            if created:
                # force creation of container...
                container = Cheers.objects.get_container(tweet)
                container.count = 1
                container.latest = parsed_date
                container.save()

