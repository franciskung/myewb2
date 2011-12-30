"""myEWB winedown twitter interface

This file is part of myEWB
Copyright 2011 Engineers Without Borders Canada
"""

import httplib, json, urllib
from datetime import datetime
from django.db.models import Max

from winedown.models import Cheers, Tweet

def load_tweets():
    since = Tweet.objects.all().aggregate(Max('twitter_id'))
    if since:
        since = since['twitter_id__max']

    conn = httplib.HTTPConnection("search.twitter.com")

    params = {'q': '@ewb OR #ewb'}  # add @ewb OR #ewb as query terms
    params['result_type'] = 'recent'        # want all recent tweets, not only popular ones...
    if since:
        params['since_id'] = since          # since is a tweet ID

    conn.request("GET", "/search.json?" + urllib.urlencode(params))
    
    response = conn.getresponse()
    if response.status != 200:
        return False

    data = response.read()
    conn.close()

    result = json.loads(data)
    for r in result['results']:
        parsed_date = datetime.strptime(r['created_at'], '%a, %d %b %Y %H:%M:%S +0000')

        tweet, created = Tweet.objects.get_or_create(twitter_id=r['id_str'],
                                                     defaults={'text': r['text'],
                                                               'author_name': r['from_user_name'],
                                                               'author_username': r['from_user'],
                                                               'author_userid': r['from_user_id'],
                                                               'author_image': r['profile_image_url'],
                                                               'date': parsed_date})
        
        if created:
            # force creation of container...
            container = Cheers.objects.get_container(tweet)
            container.count = 1
            container.latest = parsed_date
            container.save()
