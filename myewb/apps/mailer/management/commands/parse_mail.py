from django.contrib.contenttypes.models import ContentType
from django.core.management.base import NoArgsCommand
from emailconfirmation.models import EmailAddress

from base_groups.models import BaseGroup
from group_topics.models import GroupTopic
from threadedcomments.models import ThreadedComment
from mailer.models import Email
from messages.models import Message

from siteutils.shortcuts import get_object_or_none
from siteutils.helpers import autolink_email

from lxml.html.clean import clean_html, autolink_html
import settings
import mailbox
import re

class Command(NoArgsCommand):
    help = "Parses all incoming mail"

    requires_model_validation = False

    def handle_noargs(self, **options):
        # open mailbox
        
        try:
            maildir_path = settings.maildir_path
        except:
            return "No maildir path set in your settings"
         
        inbox = mailbox.Maildir(maildir_path)
        #inbox = mailbox.mbox('/var/mail/francis')
        
        inbox.lock()
        
        # iterate through all items in mailbox...
        try:
            for key, msg in inbox.iteritems():
                parse_message(key, msg)
                
                #break
                inbox.remove(key)
                
        finally:
            inbox.flush()
            inbox.unlock()
            inbox.close()
        
class BounceException(Exception):
    pass
        
def parse_message(key, msg):
        # parse subject
        subject = msg['subject']
        
        # parse author: find myEWB user based on email address
        author = parse_author(msg['from'])
        
        # parse recipient: find destination group based on "to" address
        group = parse_recipient(msg['to'])
        
        # find parent message(s)
        parent_object, parent_type = parse_references(msg['references'])
        
        # parse body of message
        body = parse_body(msg)
            
        # ok, we now have enough info, between slug and parent_obj, to 
        # hopefully do something intelligent.
        try:
            if parent_object:
                if parent_type == ContentType.objects.get_for_model(GroupTopic):
                    add_reply(parent_object, group, author, body)
                   
                elif parent_type == ContentType.objects.get_for_model(ThreadedComment):
                    add_reply(parent_object.content_object, group, author, body)
                   
                elif parent_type == ContentType.objects.get_for_model(Message):
                    add_private_msg(parent_object, author, msg)
                
            elif group:
                add_post(group, author, subject, body)
                
            else:
                raise BounceException("I don't know what to do...")
            
        except BounceExceptione as e:
            # bounce it!
            pass
        
# takes an email author, in the "Name <email>" format, and finds the associated user    
def parse_author(author):
    pattern = '(?:.*<)?([^>]*)(?:>.*)?'
    email = re.findall(pattern, author)
    
    if len(email):
        users = EmailAddress.objects.get_users_for(email[0])
        
        if len(users):
            # only one use should ever be returned, since we don't allow
            # the same verified address to be apart of multiple accounts
            return users[0]
        else:
            raise BounceException("I was unable to find a myEWB user with the email address %s" % email[0])

    raise BounceException("I wasn't able to understand the email address %s" % author)

# takes an email recipient, in "Name <email>" format, and finds the associated
# group (if any)
def parse_recipient(recipient):
    pattern = '(?:.*<)?([^>@]*)@my.ewb.ca(?:>.*)?'      # TODO: un-hardcode the my.ewb.ca domain!
    slug = re.findall(pattern, recipient)
    
    if len(slug):
        group = get_object_or_none(BaseGroup, slug=slug[0])
        
        if group:
            return group
        
    # TODO: modify to handle private-message replies
    raise BounceException("I wasn't able to figure out which group you want to post to!")

# takes the References line in email headers, and looks for any parent emails in the thread
# returns a 2-tuple of the parent object and object type (or None, None)
def parse_references(references):
    pattern = '<(.*)>\s*'
    parent_ids = re.findall(pattern, references)
    parent_emails = Email.objects.filter(message_id__in=parent_ids)
    
    parent_objects = {}
    for email in parent_email:
        if email.content_object:
            #parent_objects[email.content_object] = True

            # if multiple parents are matched, we only take the first. 
            # does this set us up for problems later...?
            # (ie, if we implement threaded replies?)
            return email.content_object, email.content_type

    return None, None

# parses the body, taking multipart/MIME and HTML messages into account,
# and doing any HTML cleaning as needed
def parse_body(msg):
    body = None
    
    if msg.is_multipart():
        html = None
        txt = None
        
        for part in msg.get_payload():
            if part.get_content_type() == 'text/html':
                html = part.get_payload()
            elif part.get_content_type() == 'text/plain':
                txt = part.get_payload()
                
        if html:
            body = html
        elif txt:
            body = txt
    
    else:
        body = msg.get_payload()
        
    if not body:
        raise BounceError("I wasn't able to understand the email you sent; it was in a format that is not supported.")
    
    # validate HTML content
    # Additional options at http://codespeak.net/lxml/lxmlhtml.html#cleaning-up-html
    body = clean_html(body)
    body = autolink_html(body)
    body = autolink_email(body)
    
    # TODO: strip out in-reference-to text in replies?
    
    return body

def add_post(group, author, subject, body):
    if not group.user_is_member(author):
        raise BounceException("You are not a member of this group; you can't post to it.")
    
    if group.members.count() > 50:
        raise BounceException("You can only reply by email to small discussion groups (less than 50 people); this prevents mistaken emails or spam from being sent to our larger mailing lists.")

    topic = GroupTopic.objects.create(group=group,
                                      send_as_email=True,
                                      title = subject,
                                      creator=author,
                                      body = body)

    sender = '"%s %s" <%s>' % (author.get_profile().first_name,
                               author.get_profile().last_name,
                               author.email)
    topic.send_email(sender=sender)

    return topic

def add_reply(parent_object, group, author, body):
    if not group.user_is_member(author):
        raise BounceException("You are not a member of this group; you can't post to it.")
    
    if group.members.count() > 50:
        raise BounceException("You can only reply by email to small discussion groups (less than 50 people); this prevents mistaken emails or spam from being sent to our larger mailing lists.")

    reply = ThreadedComment.objects.create(content_object=parent_object,
                                           user=author,
                                           comment=body)
    
    reply.send_to_watchlist()
    
    return reply
