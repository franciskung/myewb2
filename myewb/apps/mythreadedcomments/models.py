"""myEWB threaded comments models

This file is part of myEWB
Copyright 2010 Engineers Without Borders Canada

@author: Francis Kung
"""

import settings
from datetime import datetime

from mailer import send_mail
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.signals import post_save
from threadedcomments.models import ThreadedComment, FreeThreadedComment
from siteutils.helpers import fix_encoding

from attachments.models import Attachment
from group_topics.models import GroupTopic, Watchlist, wiki_convert

def send_to_watchlist(self):
    """
    Sends an email to everyone who is watching this thread, and/or to post owner.
    
    We assume that comments can only be made on topics, which is technically
    false (it uses a generic foreign key) - but in our use of it, it holds.
    Will need to change this function if we ever decide to allow comments
    on other types of objects.
    """
    
    # only run this if it is attached to a GroupTopic
    # (yeah, this is bad design... TODO refactor to be cleaner)
    topic_type = ContentType.objects.get_for_model(GroupTopic)
    if self.content_type != topic_type:
        return False

    # build email
    topic = self.content_object
    attachments = Attachment.objects.attachments_for_object(self)
    ctx = {'group': topic.group,
           'title': topic.title,
           'topic_id': topic.pk,
           'reply_id': self.pk,
           'event': None,
           'attachments': attachments
          }
          
    if topic.group.group_type == 'd':
        sender = '"%s %s" <%s>' % (self.user.get_profile().first_name,
                                   self.user.get_profile().last_name,
                                   self.user.email)
        reply_to = self.user.email
            
        topic.group.send_mail_to_members(topic.title, self.comment, sender=sender,
                                        context=ctx, content_object=self,
                                        reply_to=reply_to)
        
    sender = 'myEWB <notices@my.ewb.ca>'
    recipients = set()
    
    # loop through watchlists and send emails
    for list in topic.watchlists.all():
        user = list.owner
        # TODO: for user in list.subscribers blah blah
        if user.get_profile().watchlist_as_emails and not user.nomail:
            recipients.add(user.email)
            
    # send email to original post creator
    if topic.creator.get_profile().replies_as_emails and not topic.creator.nomail:
        recipients.add(topic.creator.email)
        
    # send email to participants
    participants = []
    allcomments = ThreadedComment.objects.all_for_object(topic)
    for c in allcomments:
        if c.user.get_profile().replies_as_emails2 and not c.user.nomail:
            recipients.add(c.user.email)
            
    # but remove original poster
    if self.user.email in recipients:
        recipients.remove(self.user.email)
    # also remove all people who've already been emailed (can this be more efficient?)
    groupmembers = set(topic.group.get_member_emails())
    recipients -= groupmembers
        
    messagebody = """<p>Hello</p>        

<p>
%s has replied to the post <em>%s</em> on myEWB:
</p>

<div style="margin: 10px; padding: 10px; border: 1px solid;">
    %s
</div>

<p>You are receiving this email because you have participated in this conversation or 
added it to your watchlist.  To change your email preferences, 
<a href="http://my.ewb.ca%s">click here</a>.
</p>
""" % (fix_encoding(self.user.visible_name()), fix_encoding(topic.title), fix_encoding(self.comment), reverse('profile_settings'))
      
    if len(recipients):
        send_mail(subject="Re: %s" % topic.title,
                  txtMessage=None,
                  htmlMessage=messagebody,
                  fromemail=sender,
                  recipients=recipients,
                  context=ctx,
                  shortname=topic.group.slug,
                  content_object=self)

ThreadedComment.send_to_watchlist = send_to_watchlist

def update_scores(sender, instance, **kwargs):
    """
    Updates the parent topic's score for the featured posts list
    """
    # only run this if it is attached to a GroupTopic
    # (yeah, this is bad design... TODO refactor to be cleaner)
    topic_type = ContentType.objects.get_for_model(GroupTopic)
    if instance.content_type != topic_type:
        return False

    topic = instance.content_object
    topic.update_score(settings.FEATURED_REPLY_SCORE)
post_save.connect(update_scores, sender=ThreadedComment, dispatch_uid='updatetopicreplyscore')

def update_reply_date(sender, instance, created, **kwargs):
    """
    Updates the parent topic's "last reply" date
    """
    # only run this if it is attached to a GroupTopic
    # (yeah, this is bad design... TODO refactor to be cleaner)
    topic_type = ContentType.objects.get_for_model(GroupTopic)
    if instance.content_type != topic_type:
        return False

    if created:
        topic = instance.content_object
        topic.last_reply = datetime.now()
        topic.save()
post_save.connect(update_reply_date, sender=ThreadedComment, dispatch_uid='updatetopicreplydate')


# add an the coniverted field directly to the ThreadedComment model
ThreadedComment.add_to_class('converted', models.BooleanField(default=True))

# and do wiki-to-HTML conversion as needed
def threadedcomment_init(self, *args, **kwargs):
    super(ThreadedComment, self).__init__(*args, **kwargs)
    
    # wiki parse if needed
    if self.pk and not self.converted and self.comment:
        self.comment = wiki_convert(self.comment)
        self.converted = True
        self.save()
ThreadedComment.__init__ = threadedcomment_init
