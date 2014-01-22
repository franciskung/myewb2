import re
from django import forms
from django.conf import settings
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponseForbidden, HttpResponseNotFound, HttpResponse
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth.views import logout as pinaxlogout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.forms import fields
from django.template import RequestContext
from django.utils.translation import ugettext, ugettext_lazy as _
try:
    from django.core.validators import email_re     # django 1.2+
except:
    from django.forms.fields import email_re        # django 1.1

from account.utils import get_default_redirect
from emailconfirmation.models import EmailAddress, EmailConfirmation
from pinax.apps.account.forms import ResetPasswordKeyForm

from account_extra.forms import EmailLoginForm, EmailSignupForm
from account.models import PasswordReset
from account.views import login as pinaxlogin
from account.views import signup as pinaxsignup
from account.forms import AddEmailForm
from base_groups.models import LogisticalGroup

from emailconfirmation.signals import email_confirmed
from siteutils import online_middleware

def login(request, form_class=EmailLoginForm, 
        template_name="account/login.html", success_url=None,
        associate_openid=False, openid_success_url=None, url_required=False):

    if not success_url:
        success_url = request.GET.get("url", None)

    next = request.GET.get("next", None)

    import urllib, urllib2, json
    url = "https://www.tigweb.org/partners/ewb/api/login.php"
    values = {'email': request.POST.get('login_name', None),
              'password': request.POST.get('password', None),
              'key': settings.EWB_TIG_API_KEY}
    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    req2 = urllib2.urlopen(req)
    response = req2.read()

    auth = json.loads(response)
	
    if auth['success']:
        userinfo = auth['userinfo']
        
        user = User.objects.get(tigid=userinfo['id'])
        
        if not user and userinfo.get('ewbid', None):
            user = User.objects.get(id=userinfo['ewbid'])
            user.tigid = userinfo['id']
            user.save()

        if not user:
            user = User.extras.create_silent_user(userinfo['email'])
            user.tigid = userinfo['id']

            profile = user.get_profile()
            if not profile.first_name:
                profile.first_name=userinfo['fname']
            if not profile.last_name:
                profile.last_name=userinfo['lname']

            user.save()
            profile.save()
        
        user.backend = "django.contrib.auth.backends.ModelBackend"
        auth_login(request, user)

        return HttpResponseRedirect(success_url)

    return render_to_response(template_name, ctx, context_instance = RequestContext(request))


def login_old(request, form_class=EmailLoginForm, 
        template_name="account/login.html", success_url=None,
        associate_openid=False, openid_success_url=None, url_required=False):
    
    if not success_url:
        success_url = request.GET.get("url", None)
        
    next = request.GET.get("next", None)
    
    return pinaxlogin(request, form_class, template_name, success_url, 
            associate_openid, openid_success_url, url_required)
    
def login_facebook(request):
    myhost = Site.objects.get_current()
    myhost = "http://%s" % myhost.domain

    if request.GET.get('code', None):
        if not request.session.get('fb_state_key', None) or not request.GET.get('state', None) or request.session['fb_state_key'] != request.GET['state']:
            return HttpResponse('disallowed')
        
        code = request.GET['code']
        request.session['fb_code'] = code
        
        return render_to_response("account/loading_redirect.html",
                                  {},
                                  context_instance=RequestContext(request))
    
    elif request.GET.get('stage', None) and request.session.get('fb_code'):
        code = request.session['fb_code']
        del(request.session['fb_code'])
        
        token_url = "https://graph.facebook.com/oauth/access_token?client_id=%s&redirect_uri=%s%s&client_secret=%s&code=%s" % \
                    (settings.FACEBOOK_APP_ID, myhost, reverse('acct_login_facebook'), settings.FACEBOOK_APP_SECRET, code)
                    
        import urllib, urlparse, simplejson, datetime
        f = urllib.urlopen(token_url)
        
        terms = urlparse.parse_qs(f.read())

        if not terms.get('access_token', None):
            return HttpResponse("Error getting a Facebook token.")

        access_token = terms['access_token']
        
        graph_url = "https://graph.facebook.com/me?access_token=%s" % access_token[0]
        f = urllib.urlopen(graph_url)

        json = f.read()
        info = simplejson.loads(json)
        
        if not info.get('verified', None):
            return HttpResponse("Sorry, your facebook account is not confirmed")
        
        if not info.get('email', None):
            return HttpResponse("Sorry, your facebook account does not have an email address - an email is required to create a myEWB account.")
        
        user = User.extras.create_silent_user(info['email'])

        profile = user.get_profile()
        if not profile.first_name:
            profile.first_name=info['first_name']
        if not profile.last_name:
            profile.last_name=info['last_name']
        if not profile.facebook_id:
            profile.facebook_id = info['id']
        if not profile.date_of_birth and info.get('birthday', None):
            profile.date_of_birth = datetime.datetime.strptime(info['birthday'], '%m/%d/%Y')
        if not profile.gender and info.get('gender', None):
            if info['gender'] == 'male':
                profile.gender = 'M'
            if info['gender'] == 'female':
                profile.gender = 'F'
        if not profile.facebook_profile_url:
            profile.facebook_profile_url = info['link']
        if not profile.raw_data:
            profile.raw_data = json
        profile.save()
        
        user.backend = "django.contrib.auth.backends.ModelBackend"
        auth_login(request, user)
        
        return render_to_response("account/finish_and_redirect.html",
                                  {},
                                  context_instance=RequestContext(request))
    
    else:
        import random, time, hashlib
        key = hashlib.md5()
        key.update("%d" % random.randint(0, 100))
        key.update("%d" % time.time())
        key.update("%d" % random.randint(0, 100))
        key = key.hexdigest()
        request.session['fb_state_key'] = key 
        
        return HttpResponseRedirect('https://www.facebook.com/dialog/oauth?client_id=%s&redirect_uri=%s%s&state=%s&scope=email,user_birthday' %
                                    (settings.FACEBOOK_APP_ID, myhost, reverse('acct_login_facebook'), key))
    
    

def signup(request, form_class=EmailSignupForm,
        template_name="account/signup.html", success_url=None,
        chapter_slug=None):
    if success_url is None:
        success_url = get_default_redirect(request)
    if request.method == "POST":
        form = form_class(request.POST,
                          chapter=chapter_slug)
        if form.is_valid():
            username, password = form.save()
            if settings.ACCOUNT_EMAIL_VERIFICATION:
                return render_to_response("account/verification_sent.html", {
                    "email": form.cleaned_data["email"],
                }, context_instance=RequestContext(request))
            else:
                user = authenticate(username=username, password=password)
                auth_login(request, user)
                
                login_message=ugettext(u"Welcome back, %(name)s") % {
                    'name': user.visible_name
                }
                request.user.message_set.create(message=login_message)
                return HttpResponseRedirect(success_url)
    else:
        form = form_class(chapter=chapter_slug)
        
    return render_to_response(template_name, {
        "form": form,
    }, context_instance=RequestContext(request))
    
def logout(request):
    online_middleware.remove_user(request)
    # TODO: leave a message saying "you've been logged out".
    # currently not possible (can't set messages for guest user) but will be
    # possible in django 1.2 
    return pinaxlogout(request, next_page=reverse('home'))

@login_required
def email(request, form_class=AddEmailForm, template_name="account/email.html",
          username=None):
    
    if username:
        if not request.user.has_module_perms("profiles"):
            return HttpResponseForbidden()
        else:
            user = get_object_or_404(User, username=username)
    else:
        user = request.user
    
    if request.method == "POST" and request.user.is_authenticated():
        if request.POST["action"] == "add":
            add_email_form = form_class(user, request.POST)
            if add_email_form.is_valid():
                add_email_form.save()
                add_email_form = form_class() # @@@
        else:
            add_email_form = form_class(user)
            if request.POST["action"] == "send":
                email = request.POST["email"]
                try:
                    email_address = EmailAddress.objects.get(
                        user=user,
                        email=email,
                    )
                    request.user.message_set.create(
                        message=_("Confirmation email sent to %(email)s") % {
                            'email': email,
                        })
                    EmailConfirmation.objects.send_confirmation(email_address)
                except EmailAddress.DoesNotExist:
                    pass
            elif request.POST["action"] == 'manual_verify':
                if request.user.has_module_perms("profiles"):
                    email = request.POST["email"]
                    try:
                        email_address = EmailAddress.objects.get(
                            user=user,
                            email=email,
                        )

                        email_address.verified = True
                        email_address.set_as_primary(conditional=True)
                        email_address.save()
                        email_confirmed.send(sender=EmailAddress, email_address=email_address)

                        request.user.message_set.create(
                            message=_("Confirmed %(email)s as a valid email") % {
                                'email': email,
                            })
                    except EmailAddress.DoesNotExist:
                        pass
                else:
                    request.user.message_set.create(message=_("You don't have permission to do this!"))
                
            elif request.POST["action"] == "remove":
                email = request.POST["email"]
                try:
                    email_address = EmailAddress.objects.get(
                        user=user,
                        email=email
                    )
                    email_address.delete()
                    request.user.message_set.create(
                        message=_("Removed email address %(email)s") % {
                            'email': email,
                        })
                except EmailAddress.DoesNotExist:
                    pass
            elif request.POST["action"] == "primary":
                email = request.POST["email"]
                email_address = EmailAddress.objects.get(
                    user=user,
                    email=email,
                )
                if user.nomail and user.bouncing:
                    user.nomail = False
                    user.bouncing = False
                    user.save()
                email_address.set_as_primary()
    else:
        add_email_form = form_class()
        
    emails = user.emailaddress_set.all().order_by('-primary', '-verified', 'email')
    mailchimp_enable = settings.MAILCHIMP_SUBSCRIBE
    return render_to_response(template_name, {
        "add_email_form": add_email_form,
        "other_user": user,
        "is_me": user == request.user,
        'emails': emails,
        'mailchimp_enable': mailchimp_enable
    }, context_instance=RequestContext(request))

def silent_signup(request, email):
    regex = re.compile(email_re)
    if not regex.search(email):
        return HttpResponseNotFound()   # invalid email

    group = get_object_or_404(LogisticalGroup, slug="silent_signup_api")
    group.add_email(email)
    return HttpResponse("success")

@login_required
def password_change(request, template_name='account/password_change.html',
                    post_change_redirect=None):
    if post_change_redirect is None:
        post_change_redirect = reverse('profile_detail', kwargs={'username': request.user.username})
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            result = request.user.set_password(form.cleaned_data['new_password1'])
            
            if not result:
                form._errors[forms.forms.NON_FIELD_ERRORS] = ["New password is too simple"]
            else:
                request.user.save()
                request.user.message_set.create(message="Password changed.")
                return HttpResponseRedirect(post_change_redirect)
    else:
        form = PasswordChangeForm(request.user)
    return render_to_response(template_name, {
        'password_change_form': form,
    }, context_instance=RequestContext(request))

def password_reset_from_key(request, key, form_class=ResetPasswordKeyForm,
        template_name="account/password_reset_from_key.html"):
    if request.method == "POST":
        password_reset_key_form = form_class(request.POST)
        if password_reset_key_form.is_valid():

            # get the password_reset object
            temp_key = password_reset_key_form.cleaned_data.get("temp_key")
            password_reset = PasswordReset.objects.filter(temp_key__exact=temp_key, reset=False)
            password_reset = password_reset[0]  # should always be safe, as form_clean checks this
    
            # now set the new user password
            user = User.objects.get(passwordreset__exact=password_reset)
            result = user.set_password(password_reset_key_form.cleaned_data['password1'])

            if not result:
                # unsuccessful
                password_reset_key_form._errors[forms.forms.NON_FIELD_ERRORS] = ["Password is too simple"]
            else:
                user.save()
                user.message_set.create(message=ugettext(u"Password successfully changed."))
        
                # change all the password reset records to this person to be true.
                for password_reset in PasswordReset.objects.filter(user=user):
                    password_reset.reset = True
                    password_reset.save()

                user = authenticate(username=user.username, password=password_reset_key_form.cleaned_data['password1'])
                auth_login(request, user)
                return HttpResponseRedirect(reverse('home'))
    else:
        password_reset_key_form = form_class(initial={"temp_key": key})

    return render_to_response(template_name, {
        "form": password_reset_key_form,
    }, context_instance=RequestContext(request))
