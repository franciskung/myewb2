"""myEWB GroupTopics views

This file is part of myEWB
Copyright 2009 Engineers Without Borders (Canada) Organisation and/or volunteer contributors
Some code derived from Pinax, copyright 2008-2009 James Tauber and Pinax Team, licensed under the MIT License

Created on: 2009-08-13
Last modified: 2009-12-02
@author: Joshua Gorner, Francis Kung
"""

import settings
from time import time

from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect, Http404
from django.utils.translation import ugettext as _
from django.utils.html import escape
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render_to_response
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.uploadhandler import TemporaryFileUploadHandler
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.db.models import Q
from emailconfirmation.models import EmailAddress

from groups import bridge

from account_extra.forms import EmailLoginForm
from base_groups.models import BaseGroup
from base_groups.helpers import user_can_adminovision, user_can_execovision
from group_topics.models import GroupTopic, Watchlist
from group_topics.forms import GroupTopicForm
from threadedcomments.models import ThreadedComment
from profiles.models import MemberProfile
from siteutils.shortcuts import get_object_or_none

from attachments.forms import AttachmentForm
from attachments.models import Attachment
from pinax.apps.topics.models import Topic
from whiteboard.models import Whiteboard

def topic(request, topic_id, group_slug=None, edit=False, template_name="topics/topic.html", bridge=None):

    topic = get_object_or_404(GroupTopic, id=topic_id)
    
    parent_group = topic.parent_group
    # XXX PERMISSIONS CHECK
    if not parent_group.is_visible(request.user) and not topic.creator == request.user:
        return render_to_response("topics/disallowed.html", {
            "topic": None,
            "group": parent_group,
            "member": None,
            "grpadmin": None,
        }, context_instance=RequestContext(request))


    # XXX PERMISSIONS CHECK
    # only the owner of a topic or a group admin can edit a topic (??)
    if (request.method == "POST" and edit == True and \
            topic.is_editable(request.user)):
        updated_body = request.POST.get('body', None)
        if updated_body is not None:
            topic.body = updated_body
            topic.save()
        return HttpResponseRedirect(topic.get_absolute_url())

    # retrieve whiteboard (create if needed)
    if topic.whiteboard == None:
        # group_slug should always be valid - group never null!
        wb = Whiteboard(title="Post%d" % (topic.id), content="")
        if topic.group:
            topic.group.associate(wb, commit=False)
        wb.save()
        topic.whiteboard = wb
        topic.save()
    
    # update "featured posts" score
    topic.update_score(settings.FEATURED_VIEW_SCORE)
        
    # find membership status
    member = False
    if request.user.is_authenticated() and topic.group and (topic.group.user_is_member(request.user) or topic.group.slug == "ewb"):
        member = True
        
    grpadmin = topic.group.user_is_admin(request.user)
    

    return render_to_response(template_name, {
        "topic": topic,
        "group": topic.group,
        "member": member,
        "grpadmin": grpadmin,
    }, context_instance=RequestContext(request))

# if group_slug=None will return all visible posts; otherwise will restrict by group
# if featured=True will sort by score; otherwise will sort by date
def topics(request, group_slug=None, form_class=GroupTopicForm,
           attach_form_class=AttachmentForm, template_name="topics/topics.html",
           bridge=None, mode=None):
    
    if request.is_ajax() or request.GET.get('ajax', None):
        template_name = "topics/topics_ajax.html"

    # kinda hack-ish.  but the easiest way; doesn't feel worth adding an AJAX param for this.
    if group_slug == 'featured':
        mode = 'featured'
        group_slug = None

    is_member = False
    group = None
    if group_slug is not None:
        group = get_object_or_404(BaseGroup, slug=group_slug)
        is_member = group.user_is_member(request.user, admin_override=True)

    if group and not group.is_visible(request.user):
        return HttpResponseForbidden()
    
    attach_count = 0
    if request.method == "POST" and group:
        return new_topic(request, group_slug)
    else:
        topic_form = form_class(instance=GroupTopic(), user=request.user, group=group)
        
        attach_forms = []
    
    # if it's a listing by group, check group visibility
    if group:
        topics = GroupTopic.objects.get_for_group(group)

    # otherwise throw up a generic listing of visible posts
    else:
        # generic topic listing: show posts from groups you're in
        # also shows posts from public groups...
        # for guests, show posts from public groups only
        topics = GroupTopic.objects.visible(user=request.user)
        
    if mode == 'featured':
        topics = GroupTopic.objects.featured(topics)
    elif mode == 'newposts' and request.user.is_authenticated():
        topics = GroupTopic.objects.since(request.user.get_profile().previous_login, qs=topics)
    elif mode == 'newreplies' and request.user.is_authenticated():
        topics = GroupTopic.objects.replies_since(request.user.get_profile().previous_login, qs=topics)

    if request.user.is_authenticated():
        can_adminovision = user_can_adminovision(request.user)
        can_execovision = user_can_execovision(request.user)
        adminovision = request.user.get_profile().adminovision
        
        if not request.user.get_profile().show_emails:
            topics = GroupTopic.objects.exclude_emails(topics)
        
    else:
        can_adminovision = False
        can_execovision = False
        adminovision = False
        
    # also kinda hackish
    if group and group.slug == "ewb":
        group = None
        mode = "frontpage"
    elif not group and not mode:
        mode = "latest" 
        
    return render_to_response(template_name, {
        "group": group,
        "topic_form": topic_form,
        "attach_forms": attach_forms,
        "attach_count": attach_count,
        "is_member": is_member,
        "topics": topics,
        "can_adminovision": can_adminovision,
        "can_execovision": can_execovision,
        "adminovision": adminovision,
        "login_form": EmailLoginForm(),                # for front-page toolbar
        "mode": mode
    }, context_instance=RequestContext(request))
    
def new_topic(request, group_slug=None, bridge=None):
    is_member = False
    group = None
    if group_slug is None:
        group_slug = "ewb"
        
    group = get_object_or_404(BaseGroup, slug=group_slug)
    is_member = group.user_is_member(request.user, admin_override=True)

    if not group.is_visible(request.user):
        return HttpResponseForbidden()
    
    attach_count = 0
    if request.method == "POST":
        if not request.user.is_authenticated():
            return HttpResponseForbidden()
        try:
            attach_count = int(request.POST.get("attach_count", 0))
        except ValueError:
            attach_count = 0
            
        if group.slug == "ewb" or is_member:
            # has been previewed.  mark it as good to go!
            if request.POST.get("previewed", None) and request.POST.get("postid", None):
                topic = GroupTopic.objects.get(id=request.POST['postid'], pending=True, creator=request.user)
                topic.pending = False
                topic.save()
                
                # extra security check that sender isn't forged.
                # can't hurt...
                sender_valid = False
                if group.user_is_admin(request.user) and request.POST.get('sender', None):
                    if request.POST['sender'] == group.from_email:
                        sender_valid = True
                        sender = '"%s" <%s>' % (group.from_name, group.from_email)
                        
                    elif get_object_or_none(EmailAddress, email=request.POST['sender']) in request.user.get_profile().email_addresses():
                        sender_valid = True
                        sender = '"%s %s" <%s>' % (request.user.get_profile().first_name,
                                                   request.user.get_profile().last_name,
                                                   request.POST['sender'])
                        
                    elif request.user.is_staff and request.POST['sender'] == "info@ewb.ca":
                        sender_valid = True
                        sender = '"EWB-ISF Canada" <info@ewb.ca>'
                        
                if topic.send_as_email:
                    if sender_valid:
                        request.user.message_set.create(message=escape("Sent as %s" % sender))
                        topic.send_email(sender=sender)
                    else:
                        request.user.message_set.create(message="Unable to send email.")
                    
                # redirect out.
                request.user.message_set.create(message=_("You have started the topic %(topic_title)s") % {"topic_title": topic.title})
                return HttpResponseRedirect(topic.get_absolute_url())
            
            # confirmation was cancelled, so delete the temp post and bump back to edit screen
            topic = None
            if request.POST.get("goback", None) and request.POST.get("postid", None):
                topic = get_object_or_none(GroupTopic, id=request.POST['postid'], pending=True, creator=request.user)
                
            if topic: 
                topic_form = GroupTopicForm(instance=topic, user=request.user, group=group)
                attach_forms = []
                topic.delete()
            
            # validate form and show preview...
            else:
                topic_form = GroupTopicForm(request.POST, user=request.user, group=group)
                attach_forms = [AttachmentForm(request.POST, request.FILES, prefix=str(x), instance=Attachment()) for x in range(0,attach_count)]
            
                # do not take blank attachment forms into account
                for af in attach_forms:
                    if not af.is_valid() and not af['attachment_file'].data:
                        attach_forms.remove(af)
                        attach_count = attach_count - 1
                
                # all good.  save it!
                if topic_form.is_valid() and all([af.is_valid() for af in attach_forms]) and not request.POST.get("goback", None):
                    # save the post but mark it as "pending".... and display a confirmation.
                    topic = topic_form.save(commit=False)
                    if group:
                        group.associate(topic, commit=False)
                    topic.creator = request.user
                    topic.pending = True
                    topic.save()
                    
                    # save the attachments.
                    # We need the "Topic" object in order to retrieve attachments properly
                    # since other functions only get the Topic object
                    base_topic = GroupTopic.objects.get(id=topic.id)
                    attachments = []
                    for af in attach_forms:
                        attachment = af.save(request, base_topic)
                        attachments.append(af.cleaned_data['attachment_file'].name)
        
                    sender = None
                    if topic_form.cleaned_data.get('send_as_email', None):
                        sender = topic_form.cleaned_data.get('sender', None)

                    is_large_group = False
                    if group.members.count() > 50:
                        is_large_group = True
        
                    return render_to_response("topics/preview.html",
                                              {"group": group,
                                               "topic": topic,
                                               "is_member": is_member,
                                               "sender": sender,
                                               "attachments": attachments,
                                               "is_large_group": is_large_group,
                                              },
                                              context_instance=RequestContext(request))
        else:
            # if they can't start a topic, why are we still loading up a form?
            request.user.message_set.create(message=_("You are not a member and so cannot start a new topic"))
            topic_form = GroupTopicForm(instance=GroupTopic())                
            attach_forms = [AttachmentForm(prefix=str(x), instance=Attachment()) for x in range(0,attach_count)]
            
    else:
        topic_form = GroupTopicForm(instance=GroupTopic(), user=request.user, group=group)
        attach_forms = []

    return render_to_response("topics/new_topic.html", {
        "group": group,
        "topic_form": topic_form,
        "attach_forms": attach_forms,
        "attach_count": attach_count,
        "is_member": is_member,
    }, context_instance=RequestContext(request))
    
def get_attachment_form(request, template_name="topics/attachment_form.html", form_class=AttachmentForm, group_slug=None, bridge=None):

    if request.is_ajax():
        attach_form = form_class(prefix=request.POST['prefix'], instance=Attachment())
        response = render_to_response(
            template_name,
            {
                'attach_form': attach_form,
            },
            context_instance=RequestContext(request),
        )
        return response
    else:
        raise Http404

def topic_delete(request, topic_id, group_slug=None, bridge=None, confirm=False):
    """
    Another copy-pasta from pinax.apps.topics.views.
    Again need to update to match our GroupTopic stuff.
    Mostly we 
    """
    if bridge:
        try:
            group = bridge.get_group(group_slug)
        except ObjectDoesNotExist:
            raise Http404
    else:
        group = None
    
    if group:
        topics = group.content_objects(Topic)
    else:
        # line below is the only change between pinax and us.
        # topics = Topic.objects.filter(object_id=None)
        topics = Topic.objects.all()

    
    topic = get_object_or_404(topics, id=topic_id)
    
    if (request.method == "POST" and (request.user == topic.creator or topic.group.user_is_admin(request.user))):
        if confirm:
            ThreadedComment.objects.all_for_object(topic).delete()
            topic.delete()
        
            return HttpResponseRedirect(request.POST["next"])
        else:
            return render_to_response("topics/topic_delete.html",
                                      {"topic": topic,
                                       "next": request.POST["next"]},
                                      context_instance=RequestContext(request)
                                     )
    else:
        return HttpResponseForbidden()

def topics_by_user(request, username):
    """
    Return a listing of all topics visible the current user, and created by
    the given user
    """
    user = get_object_or_404(User, username=username)

    if request.user == user:
        # user can always see their own post, regardless of group visibility
        # (ie, if I write some posts to a private group then leave the group, 
        #  those posts should still show in this listing)
        topics = GroupTopic.objects.get_for_user(user)
        
    else:
        # start with all visible topics
        topics = GroupTopic.objects.visible(request.user)
            
        # then restrict further to only ones by the given user
        topics = GroupTopic.objects.get_for_user(user, topics)
            
    return render_to_response("topics/topics.html",
                              {"topics": topics,
                               "group": None,
                               "mode": "byuser-%s" % username,
                               "hideheader": True},
                              context_instance=RequestContext(request)
                             )

def adminovision_toggle(request, group_slug=None):
    """
    Toggles admin-o-vision for the current user.
    No effect if user is not an admin
    """

    if user_can_adminovision(request.user) | user_can_execovision(request.user):
        profile = request.user.get_profile()
    
        profile.adminovision = not profile.adminovision
        profile.save()
    
    # this redirect should be OK, since the adminovision link is only visible from reverse('home')
    return HttpResponseRedirect(reverse('home'))

def watchlist(request, list_id):
    """
    Displays post listing in the given watchlist
    """
    list = get_object_or_404(Watchlist, pk=list_id)

    topics = GroupTopic.objects.get_for_watchlist(list)
            
    return render_to_response("topics/topics.html",
                              {"topics": topics,
                               "group": None,
                               "mode": "watchlist-%s" % list_id,
                               "hideheader": True},
                              context_instance=RequestContext(request)
                             )
    
def watchlist_index(request):
    """
    Displays list of watchlists belonging to user
    """
    
    # TODO: this will all change when we allow multiple lists per user...
    list, created = Watchlist.objects.get_or_create(owner=request.user,
                                                    defaults={'name': 'watchlist'})
    return watchlist(request, list.pk)

#def add_to_watchlist(request, list_id, topic_id):
def add_to_watchlist(request, user_id, topic_id):
    """
    Adds the specified topic to the watchlist.
    Meant to be an AJAX call.
    """
    #list = get_object_or_404(Watchlist, pk=list_id)
    user = get_object_or_404(User, pk=user_id)
    list, created = Watchlist.objects.get_or_create(owner=user,
                                                    defaults={'name': 'watchlist'})
    topic = get_object_or_404(GroupTopic, pk=topic_id)
    
    if list.user_can_control(request.user):
        list.add_post(topic)
        request.session['cache_stamp'] = time()
        
        # TODO: do I want to templatize?
        return HttpResponse("[remove from watch-list]")
    else:
        return HttpResponse("error! =(")

def remove_from_watchlist(request, user_id, topic_id):
    """
    Removes the specified topic from the watchlist.
    Meant to be an AJAX call.
    """
    #list = get_object_or_404(Watchlist, pk=list_id)
    user = get_object_or_404(User, pk=user_id)
    list = get_object_or_404(Watchlist, owner=user)
    topic = get_object_or_404(GroupTopic, pk=topic_id)
    
    if list.user_can_control(request.user):
        list.remove_post(topic)
        request.session['cache_stamp'] = time()
        
        # TODO: do I want to templatize?  do you!  just kidding. -sean  @@@
        return HttpResponse("[add to watch-list]")  # was "removed"
    else:
        return HttpResponse("error! =(")

def update_modifier(request, topic_id):
    """
    Updates the "featured post" score modifier - admins can use this to 
    bump specific posts...
    """
    if request.user.has_module_perms("group_topics") and request.method == 'POST':
        value = request.POST.get("value", "")
        
        try:
            modifier = int(value)
        except:
            return HttpResponse("invalid number")
            
        topic = get_object_or_404(GroupTopic, pk=topic_id)
        topic.update_modifier(modifier)
            
        return HttpResponse(topic.score)
    else:
        return HttpResponse("denied")
