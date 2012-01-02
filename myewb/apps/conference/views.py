"""myEWB conference registration views

This file is part of myEWB
Copyright 2009 Engineers Without Borders Canada

Created on: 2009-10-18
@author: Francis Kung
"""

import csv, locale
from datetime import date

from django.contrib import auth
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db.models import Sum
from django.http import HttpResponseRedirect, HttpResponseForbidden, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib.contenttypes.models import ContentType
from attachments.models import Attachment

from account_extra.forms import EmailLoginForm, EmailSignupForm

from base_groups.models import BaseGroup
from conference.decorators import conference_login_required
from conference.forms import * #ConferenceRegistrationForm, CodeGenerationForm, ConferenceSignupForm #ConferenceRegistrationFormPreview, 
from conference.models import ConferenceRegistration, ConferenceCode
from conference.constants import *
from conference.utils import needsToRenew
from networks.models import ChapterInfo
from profiles.models import MemberProfile
from profiles.forms import AddressForm
from siteutils.shortcuts import get_object_or_none
from siteutils.decorators import owner_required, secure_required
from siteutils.helpers import fix_encoding

@secure_required
def login(request):
    
    signin_form = EmailLoginForm()
    signup_form = ConferenceSignupForm()
    
    if request.method == "POST" and request.POST.get('action', None):
        if request.POST['action'] == 'signin':
            signin_form = EmailLoginForm(request.POST)
            if signin_form.is_valid():
                user = signin_form.user
                user.is_bulk = False
                user.save()
                auth.login(request, user)

                if request.POST.get('language', 'english') == 'french':
                    request.session['conflang'] = 'fr'
                    request.session['django_language'] = 'fr'
                    locale.setlocale(locale.LC_ALL, 'fr_FR')
                else:
                    request.session['conflang'] = 'en'
                    request.session['django_language'] = 'en'
                    locale.setlocale(locale.LC_ALL, 'en_US')
                
                return HttpResponseRedirect(reverse('confreg'))
        else:
            signup_form = ConferenceSignupForm(request.POST)
            
            if signup_form.is_valid():
                username, password = signup_form.save()
                user = auth.authenticate(username=username, password=password)
                auth.login(request, user)

                if request.META['SERVER_NAME'] == 'conference2012.ewb.ca':
                    return HttpResponseRedirect(reverse('conference_questionnaire'))
                else:
                    return HttpResponseRedirect(reverse('confreg'))
        
    return render_to_response('conference/login.html',
                              {"signin_form": signin_form,
                               "signup_form": signup_form},
                              context_instance = RequestContext(request))

@secure_required
@conference_login_required()
def view_registration(request):
    user = request.user
    stage = None
    form = None
    
    try:
        # if already registered, we display "thank you" page and offer
        # cancellation or a receipt
        registration = ConferenceRegistration.objects.get(user=user, submitted=True, cancelled=False)
        
        if registration.tshirt and registration.tshirt != 'n':
            tshirtform = None
        else:
            tshirtform = True

        if registration.ski:
            skiform = None
        else:
            skiform = True

        #return HttpResponseRedirect(reverse('confcomm_app'))
        return render_to_response('conference/postregistration.html',
                                  {'registration': registration,
                                   'tshirtform': tshirtform,
                                   'skiform': skiform,
                                   'user': request.user,
                                  },
                                  context_instance=RequestContext(request)
                                 )
        

    except ObjectDoesNotExist:
        # if not registered, we display the registration form
        registration = get_object_or_none(ConferenceRegistration, user=user, submitted=False, cancelled=False)
        
        stage = request.POST.get('reg_stage', None)
        if not stage:
            stage = request.GET.get('reg_stage', None)
        
        if request.method == 'POST':
            
            # populate and process the right registration form...
            if not stage:
                form = ConferenceRegistrationForm1(request.POST, instance=registration)
            elif stage == '2':
                form = ConferenceRegistrationForm2(request.POST, instance=registration)
            elif stage == '3':
                form = ConferenceRegistrationForm3(request.POST, instance=registration)
            elif stage == '4':
                form = ConferenceRegistrationForm4(request.POST, instance=registration)
                
            form.user = user
            if form.is_valid():
                form_valid = True
                registration = form.save(commit=False)
                registration.user = user
                registration.save()
                
                # advance the stage counter and find next action
                if not stage:
                    stage = '2'
                elif stage == '2':
                    stage = '3'
                elif stage == '3':
                    stage = '4'
                elif stage == '4':
                    return ConferenceRegistrationFormPreview(ConferenceRegistrationForm4)(request, username=request.user.username, registration_id=registration.id)
                
                form = None

        # populate form (either current form with errors, or next stage's form)
        if not stage and not form:
            form = ConferenceRegistrationForm1(instance=registration)
        elif stage == '2' and not form:
            form = ConferenceRegistrationForm2(instance=registration)
        elif stage == '3' and not form:
            form = ConferenceRegistrationForm3(instance=registration)
        elif stage == '4' and not form:
            form = ConferenceRegistrationForm4(instance=registration)
        form.user = request.user
                
    needsRenewal = needsToRenew(request.user.get_profile())

    last_stage = None
    if stage == '3':
        last_stage = '2'
    elif stage == '4':
        last_stage = '3'
    elif stage == '5':
        last_stage = '4'

    return render_to_response('conference/registration.html',
                              {'registration': registration,
                               'form': form,
                               'stage': stage,
                               'last_stage': last_stage,
                               'user': request.user,
                               'needsRenewal': needsRenewal
                              },
                              context_instance=RequestContext(request)
                             )
    
@secure_required
@conference_login_required()
def registration_preview(request):
    username = request.user.username
    
    f = ConferenceRegistrationForm(request.POST, request.FILES)
    f.user = request.user
    if f.is_valid():
        if f.cleaned_data.get('resume', None):
            resume = Attachment()
            resume.creator = request.user
            resume.content_type = ContentType.objects.get_for_model(request.user)
            resume.object_id = request.user.id
            resume.attachment_file = f.cleaned_data['resume']
            resume.save()
            
    return ConferenceRegistrationFormPreview(ConferenceRegistrationForm)(request, username=username)

@secure_required
@conference_login_required()
def purchase_tshirt(request):
    registration = get_object_or_none(ConferenceRegistration, user=request.user, submitted=True, cancelled=False)

    if not registration:
        request.user.message_set.create("You aren't registered for conference...")
        return HttpResponseRedirect(reverse('confreg'))
    
    if request.method == 'POST':
        return ConferenceTShirtFormPreview(ConferenceTShirtForm)(request, username=request.user.username, registration_id=registration.id)
    
    else:
        tshirtform = ConferenceTShirtForm(initial={'id': registration.id})
        tshirtform.user = request.user

    return render_to_response('conference/purchase.html',
                              {'registration': registration,
                               'form': tshirtform,
                               'user': request.user,
                              },
                              context_instance=RequestContext(request)
                             )
    
@secure_required
@conference_login_required()
def purchase_ski(request):
    registration = get_object_or_none(ConferenceRegistration, user=request.user, submitted=True, cancelled=False)

    if not registration:
        request.user.message_set.create("You aren't registered for conference...")
        return HttpResponseRedirect(reverse('confreg'))
    
    if request.method == 'POST':
        return ConferenceSkiFormPreview(ConferenceSkiForm)(request, username=request.user.username, registration_id=registration.id)
    
    else:
        skiform = ConferenceSkiForm(initial={'id': registration.id})
        skiform.user = request.user

    return render_to_response('conference/purchase.html',
                              {'registration': registration,
                               'form': skiform,
                               'user': request.user,
                              },
                              context_instance=RequestContext(request)
                             )
    
@secure_required
@conference_login_required()
def purchase_ad(request):
    registration = get_object_or_none(ConferenceRegistration, user=request.user, submitted=True, cancelled=False)

    if not registration:
        request.user.message_set.create("You aren't registered for conference...")
        return HttpResponseRedirect(reverse('confreg'))
    
    if request.method == 'POST':
        return ConferenceADFormPreview(ConferenceADForm)(request, username=request.user.username, registration_id=registration.id)

    else:
        form = ConferenceADForm(initial={'id': registration.id})
        form.user = request.user

    return render_to_response('conference/purchase.html',
                              {'registration': registration,
                               'form': form,
                               'user': request.user,
                              },
                              context_instance=RequestContext(request)
                             )
        
@secure_required
@conference_login_required()
def resume(request):
    registration = get_object_or_none(ConferenceRegistration, user=request.user, submitted=True, cancelled=False)

    if not registration:
        request.user.message_set.create("You aren't registered for conference...")
        return HttpResponseRedirect(reverse('confreg'))
    
    if request.method == 'POST':
        form = ConferenceResumeForm(request.POST, request.FILES)
        if form.is_valid():
            resume = Attachment()
            resume.creator = request.user
            resume.content_type = ContentType.objects.get_for_model(registration)
            resume.object_id = registration.id
            resume.attachment_file = form.cleaned_data['resume']
            resume.save()
            
            request.user.message_set.create(message="Thank you!")
            return HttpResponseRedirect(reverse('confreg'))
    else:
        form = ConferenceResumeForm()
                
    return render_to_response('conference/resume.html',
                              {'registration': registration,
                               'form': form,
                               'user': request.user,
                              },
                              context_instance=RequestContext(request)
                             )
        
@conference_login_required()
def receipt(request):

    try:
        registration = ConferenceRegistration.objects.get(user=request.user, submitted=True, cancelled=False)

    except ObjectDoesNotExist:
        #message = loader.get_template("profiles/suggest_network.html")
        #c = Context({'network': network, 'action': 'join'})
        #request.user.message_set.create(message=message.render(c))
        request.user.message_set.create(message="You are not registered")
        
        return HttpResponseRedirect(reverse('confreg'))

    return render_to_response('conference/receipt.html',
                              {'reg': registration},
                              context_instance=RequestContext(request)
                             )
        
@conference_login_required()
def cancel(request):
    try:
        registration = ConferenceRegistration.objects.get(user=request.user, submitted=True, cancelled=False)

    except ObjectDoesNotExist:
        #message = loader.get_template("profiles/suggest_network.html")
        #c = Context({'network': network, 'action': 'join'})
        #request.user.message_set.create(message=message.render(c))
        request.user.message_set.create(message="You are not registered")
        
        return HttpResponseRedirect(reverse('confreg'))

    # a post request indicates that they've seen the confirm page...
    if request.method == 'POST':
        registration.cancel()
        registration.save()
        
        # send an email to myself to manually refund the registration fee
        body = "Conference registration cancelled.\n\n"
        body += "Name: " + registration.user.first_name + " " + registration.user.last_name+ "\n"
        body += "Transaction ID: " + registration.txid + "\n"
        body += "Receipt number: " + registration.receiptNum + "\n\n"
        
        body += "Refund amount: %s" % registration.getRefundAmount()
        
        send_mail('Confreg cancelled', body, 'mailer@my.ewb.ca',
                  ['monitoring@ewb.ca'], fail_silently=False)

        cancelled = True
    else:
        cancelled = False
        
    # this template will show a confirm page.
    return render_to_response('conference/cancel.html',
                              {'reg': registration,
                               'cancelled': cancelled},
                               context_instance=RequestContext(request)
                               )
    
@conference_login_required()
def list(request, chapter=None):
    if chapter == None:
        
        # would be pretty easy to exnted this to provide listings from
        # any group, not just a chapter.
        chapters = ChapterInfo.objects.all()
        
        if not request.user.has_module_perms('conference'):
            # non-admins: only see chapters you're an exec of
            chapters = chapters.filter(network__members__user=request.user,
                                       network__members__is_admin=True)

        # if only one chapter, display it right away
        if chapters.count() == 1:
            chapter = chapters[0].network.slug

        else:
            # otherwise, show a summary page
            for chapter in chapters:
                registrations = ConferenceRegistration.objects.filter(user__memberprofile__chapter=chapter.network,
                                                                      submitted=True, cancelled=False)
                chapter.numRegistrations = registrations.count()
            
            stats = {}
            if request.user.has_module_perms('conference'):
                reg = ConferenceRegistration.objects.filter(submitted=True, cancelled=False)
                stats['total_registration'] = reg.count()
                stats['external_registration'] = reg.filter(user__is_bulk=True).count()
                
                all_fees = reg.aggregate(Sum('amountPaid'), Sum('africaFund'))
                stats['reg_fees'] = all_fees['amountPaid__sum']
                stats['africafund'] = all_fees['africaFund__sum']
                if stats['total_registration']:
                    stats['africafund_percent'] = reg.filter(africaFund__isnull=False).count() * 100 / stats['total_registration']
                else:
                    stats['africafund_percent'] = 0
                stats['male'] = reg.filter(user__memberprofile__gender='M').count()
                if stats['africafund_percent']:
                    stats['male_percent'] = stats['male'] * 100 / stats['total_registration']
                else:
                    stats['male_percent'] = 0
                stats['female'] = reg.filter(user__memberprofile__gender='F').count()
                if stats['africafund_percent']:
                    stats['female_percent'] = stats['female'] * 100 / stats['total_registration']
                else:
                    stats['female_percent'] = 0
            
                reg = reg.filter(user__is_bulk=False)
                stats['member_registration'] = reg.filter(code__isnull=False).count()
                
                reg = reg.filter(code__isnull=True) 
                stats['open_registration'] = reg.filter(type__contains='open').count()
                stats['alumni_registration'] = reg.filter(type__contains='alumni').count()
                
            return render_to_response('conference/select_chapter.html',
                                      {'chapters': chapters,
                                       'stats': stats,
                                       'is_admin': request.user.has_module_perms('conference')},
                                      context_instance=RequestContext(request)
                                      )
    
    # so... by mangling the slug, you *can* actually see listings from all
    # groups you're an admin of! ;-)
    group = get_object_or_404(BaseGroup, slug=chapter)
    
    # permissions chcek!
    if not group.user_is_admin(request.user) and not request.user.has_module_perms('conference'):
        return render_to_response('denied.html', context_instance=RequestContext(request))
        
    registrations = ConferenceRegistration.objects.filter(user__memberprofile__chapter=group,
                                                          submitted=True, cancelled=False)

    return render_to_response('conference/list.html',
                              {'registrations': registrations,
                               'group': group},
                               context_instance=RequestContext(request)
                               )
    
def download(request, who=None):
    if not request.user.has_module_perms('conference'):
        return render_to_response('denied.html', context_instance=RequestContext(request))
    
    reg = ConferenceRegistration.objects.filter(submitted=True, cancelled=False)
    
    if who == 'chapter':
        reg = reg.filter(user__is_bulk=False, code__isnull=False)
    elif who == 'open':
        reg = reg.filter(user__is_bulk=False, type__contains='open')
    elif reg == 'alumni':
        reg = reg.filter(user__is_bulk=False, type__contains='alumni')
    elif reg == 'external':
        reg = reg.filter(user__is_bulk=True)
        
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=confreg_%s_%d-%d-%d.csv' % (who, date.today().month, date.today().day, date.today().year)
    
    writer = csv.writer(response)
    writer.writerow(['First name', 'Last name', 'Email',
                     'Gender', 'Language', 'Chapter', 'amount paid',
                     'room size', 'registered on', 'headset',
                     'food prefs', 'special needs',
                     'emergency name', 'emergency phone', 'prev conferences',
                     'prev retreats', 'cell phone', 't-shirt', 'ski trip',
                     'reg code', 'reg type', 'african delegate',
                     'roommate request', 'new to ottawa', 
                     'Survey - learn', 'Survey - connections', 'Survey - opportunities and challenges',
                     'Survey - perfect experience', 'Survey - stay up to speed',
                     'Survey - Sunday trip', 'Survey - socials', 'Survey - restaurants'
                     ])
    
    for r in reg:
        fname = r.user.first_name
        lname = r.user.last_name
        email = r.user.email
        gender = r.user.get_profile().gender
        language = r.user.get_profile().language
        if r.user.get_profile().get_chapter():
            chapter = r.user.get_profile().get_chapter().name
        else:
            chapter = ''
        if r.code:
            code = r.code.code
        else:
            code = ''
            
        row = [fname, lname, email, gender, language, chapter,
               r.amountPaid, r.roomSize, r.date, r.headset,
               r.foodPrefs, r.specialNeeds, r.emergName, r.emergPhone,
               r.prevConfs, r.prevRetreats, r.cellphone, r.tshirt, r.ski,
               code, r.type, r.africaFund, r.roommate, r.new_to_ottawa,
               r.survey1, r.survey2, r.survey3, r.survey4,
               r.survey5, r.survey6, r.survey7, r.survey8]
            
        writer.writerow([fix_encoding(s) for s in row])

    return response

def generate_codes(request):
    # ensure only admins...
    if request.user.has_module_perms('conference'):
        codes = []
    
        if request.method == 'POST':
            form = CodeGenerationForm(request.POST)
        
            if form.is_valid():
                start = form.cleaned_data['start'] 
                number = form.cleaned_data['number']
                type  = form.cleaned_data['type']
            
                # iterate through request codes, generating and saving to 
                # database if needed
                for i in range (start, start + number):
                    code = ConferenceCode(type=type, number=i)
                
                    code, created = ConferenceCode.objects.get_or_create(type=type, number=i, code=code.code)

                    if request.POST.get('action', None) == "void":
                        
                        code.expired = True
                        code.save()
                        codes.append("voided - " + code.code)
                    else:
                        codes.append(code.code)

                form = CodeGenerationForm()
        
        else:
            form = CodeGenerationForm()
        
        return render_to_response('conference/codes.html',
                                  {'codes': codes,
                                   'form': form,
                                   'conf_codes': CONF_CODES,
                                   'conf_options': CONF_OPTIONS,
                                   'room_choices': ROOM_CHOICES
                                  },
                                  context_instance=RequestContext(request)
                                 )
    else:
        # we've gotten be more standard on whether we render a denied page,
        # or return HttpResponseForbidden - and, eventually, make the UI better
        # in either case.
        return render_to_response('denied.html', context_instance=RequestContext(request))

def lookup_code(request):
    if request.user.has_module_perms('conference'):
        if request.method == 'POST' and request.POST.get('code', None):
            code = get_object_or_none(ConferenceCode, code=request.POST['code'])
            
            if code and code.expired:
                return HttpResponse("voided")
            elif code:
                reg = ConferenceRegistration.objects.filter(code=code, submitted=True, cancelled=False)
                if reg.count():
                    return HttpResponse("used")
                else:
                    return HttpResponse("available")
            else:
                if ConferenceCode.isValid(request.POST['code']):
                    return HttpResponse("not issued")
                else:
                    return HttpResponse("invalid code")
    return HttpResponse("lookup error")
    
