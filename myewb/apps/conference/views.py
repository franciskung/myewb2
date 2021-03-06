"""myEWB conference registration views

This file is part of myEWB
Copyright 2009 Engineers Without Borders Canada

Created on: 2009-10-18
@author: Francis Kung
"""

import csv
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

from base_groups.models import BaseGroup, GroupMemberRecord
from communities.models import NationalRepList
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
                    request.session['django_language'] = 'fr_FR'
                else:
                    request.session['conflang'] = 'en'
                    request.session['django_language'] = 'en_US'
                
                return HttpResponseRedirect(reverse('confreg'))
        else:
            signup_form = ConferenceSignupForm(request.POST)
            
            if signup_form.is_valid():
                username, password = signup_form.save()
                user = auth.authenticate(username=username, password=password)
                auth.login(request, user)

                if request.META['SERVER_NAME'] == 'conference2013.ewb.ca':
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
        
        """
        if registration.tshirt and registration.tshirt != 'n':
            tshirtform = None
        else:
            tshirtform = True

        if registration.extra_gala:
            skiform = None
        else:
            skiform = True
        """

        #return HttpResponseRedirect(reverse('confcomm_app'))
        return render_to_response('conference/postregistration.html',
                                  {'registration': registration,
                                   #'tshirtform': tshirtform,
                                   #'skiform': skiform,
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
                form = ConferenceRegistrationProfileForm(request.POST, instance=user.get_profile())
            elif stage == '2':
                form = ConferenceRegistrationForm1(request.POST, instance=registration)
            elif stage == '3':
                form = ConferenceRegistrationForm2(request.POST, instance=registration)
            elif stage == '4':
                form = ConferenceRegistrationForm3(request.POST, instance=registration)
            elif stage == '5':
                form = ConferenceRegistrationForm4(request.POST, instance=registration)
            elif stage == '6':
                form = ConferenceRegistrationForm5(request.POST, instance=registration)
            elif stage == '7':
                form = ConferenceRegistrationForm6(request.POST, instance=registration)
            elif stage == '8':
                form = ConferenceRegistrationForm7(request.POST, instance=registration)
            elif stage == '9':
                form = ConferenceRegistrationForm8(request.POST, instance=registration)
                
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
                    if registration.hotel == 'hotelquad' or registration.hotel == 'hoteldouble' or (registration.code and registration.code.type == 'q'):
                        stage = '5'
                    else:
                        stage = '6'
                elif stage == '5':
                    stage = '6'
                elif stage == '6':
                    stage = '7'
                elif stage == '7':
                    stage = '8'
                elif stage == '8':
                    stage = '9'
                elif stage == '9':
                    return ConferenceRegistrationFormPreview(ConferenceRegistrationForm8)(request, username=request.user.username, registration_id=registration.id)
                
                form = None

        # populate form (either current form with errors, or next stage's form)
        if not stage and not form:
            form = ConferenceRegistrationProfileForm(instance=user.get_profile())
        elif stage == '2' and not form:
            form = ConferenceRegistrationForm1(instance=registration)
        elif stage == '3' and not form:
            form = ConferenceRegistrationForm2(instance=registration)
        elif stage == '4' and not form:
            form = ConferenceRegistrationForm3(instance=registration)
        elif stage == '5' and not form:
            form = ConferenceRegistrationForm4(instance=registration)
        elif stage == '6' and not form:
            form = ConferenceRegistrationForm5(instance=registration)
        elif stage == '7' and not form:
            form = ConferenceRegistrationForm6(instance=registration)
        elif stage == '8' and not form:
            form = ConferenceRegistrationForm7(instance=registration)
        elif stage == '9' and not form:
            form = ConferenceRegistrationForm8(instance=registration)
        form.user = request.user
                
    needsRenewal = needsToRenew(request.user.get_profile())

    last_stage = None
    if stage == '3':
        last_stage = '2'
    elif stage == '4':
        last_stage = '3'
    elif stage == '5':
        last_stage = '4'
    elif stage == '6':
        if registration.hotel == 'hotelquad' or registration.hotel == 'hoteldouble' or (registration.code and registration.code.type == 'q'):
            last_stage = '5'
        else:
            last_stage = '4'
    elif stage == '7':
        last_stage = '6'
    elif stage == '8':
        last_stage = '7'
    elif stage == '9':
        last_stage = '8'

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
                              {'reg': registration,
                               'typename': CONF_OPTIONS[registration.type]['name'],
                               'typecost': CONF_OPTIONS[registration.type]['cost'],
                               'hotelname': HOTEL_OPTIONS[registration.hotel]['name'],
                               'hotelcost': HOTEL_OPTIONS[registration.hotel]['cost'],
                               },
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

    """
    is_president = False
    prez_group = NationalRepList.objects.get(slug='presidents')
    pro_prez_group = NationalRepList.objects.get(slug='citynetworkpres')
    if request.user.has_module_perms('conference'):
        is_president = True
    else:
        if group.user_is_admin(request.user):
            if prez_group.user_is_member(request.user) or pro_prez_group.user_is_member(request.user):
                is_president = True

    ldd, created = LeadershipDaySpots.objects.get_or_create(chapter=group)
    ldd_open = ldd.spots - ConferenceRegistration.objects.filter(submitted=True, cancelled=False, ldd_chapter=group).count()
    """

    return render_to_response('conference/list.html',
                              {'registrations': registrations,
                               'group': group,
                               #'is_president': is_president,
                               #'ldd_total': ldd.spots,
                               #'ldd_open': ldd_open},
                               },
                               context_instance=RequestContext(request)
                               )
    
def download(request, who=None):
    if not request.user.has_module_perms('conference'):
        return render_to_response('denied.html', context_instance=RequestContext(request))
    
    reg = ConferenceRegistration.objects.filter(submitted=True, cancelled=False)
    
    if who == 'chapter':
        reg = reg.filter(type='ewb')
    elif reg == 'alumni':
        reg = reg.filter(type='alumni')
        
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=confreg_%s_%d-%d-%d.csv' % (who, date.today().month, date.today().day, date.today().year)
    
    writer = csv.writer(response)
    writer.writerow(['First name', 'Last name', 'Email',
                     'Gender', 'Language',
                     'Who Are You', 'Nametag name', 'Nametag org',
                     'emergency name', 'emergency phone', 'emergency reln',
                     'Medical concerns', 'Chapter', 'Role', 'Childcare', 'Childcare contact',
                     'Accessibility needs', 'Headset', 'Prev conf', 'Prev retreat',
                     'Registration type', 'Registration code', 'Hotel option',
                     'Hotel - gender', 'Hotel - sleeping', 'Roommates', 'Hotel requests',
                     'Food prefs', 'Dietary', 'Special needs', 'Bracelet', 'Handbook',
                     'Kumvana', 'Leadership day applicaion'])
                     
    for r in reg:
        fname = r.user.first_name
        lname = r.user.last_name
        email = r.user.email
        gender = r.user.get_profile().gender
        language = r.user.get_profile().language
        if r.code:
            code = r.code.code
        else:
            code = ''

        row = [fname, lname, email, gender, language, 
               r.whoareyou, r.nametag, r.nametag_org,
               r.emergName, r.emergPhone, r.emergReln,
               r.medical, r.chapter, r.role, r.childcare, r.childcare_contact,
               r.accessibility, r.headset, r.prevConfs, r.prevRetreats,
               r.type, code, r.hotel,
               r.hotelgender, r.hotelsleep, r.hotelroommates, r.hotelrequests,
               r.foodPrefs, r.dietary, r.specialNeeds, r.bracelet, r.handbook,
               r.africaFund, r.leadership_day]
            
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

        chapters = ChapterInfo.objects.all().order_by('chapter_name')
        
        """
        for c in chapters:
            l, created = LeadershipDaySpots.objects.get_or_create(chapter=c.network)
            used = ConferenceRegistration.objects.filter(submitted=True, cancelled=False, ldd_chapter=c.network)
            c.ldd = used.count()

        ldd = LeadershipDaySpots.objects.all()
        """
        
        return render_to_response('conference/codes.html',
                                  {'codes': codes,
                                   'form': form,
                                   'conf_codes': CONF_CODES,
                                   'conf_options': CONF_OPTIONS,
#                                   'room_choices': ROOM_CHOICES,
#                                   'ldd': ldd,
                                   'chapters': chapters
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
    
def ldd_spots(request):
    if request.user.has_module_perms('conference'):
        if request.method == 'POST':
            chapters = ChapterInfo.objects.all().order_by('chapter_name')

            for c in chapters:
                l, created = LeadershipDaySpots.objects.get_or_create(chapter=c.network)

                spots = request.POST.get("ldd_%d" % c.network.id, 0)
                l.spots = spots
                l.save()

            request.user.message_set.create(message='LDD spots updated')            

        return HttpResponseRedirect(reverse('conference_codes'))

    else:
        return render_to_response('denied.html', context_instance=RequestContext(request))

def ldd_delegates(request, chapter_id):
    chapter = BaseGroup.objects.get(id=chapter_id)

    is_president = False
    prez_group = NationalRepList.objects.get(slug='presidents')
    pro_prez_group = NationalRepList.objects.get(slug='citynetworkpres')
    if request.user.has_module_perms('conference'):
        is_president = True
    else:
        if chapter.user_is_admin(request.user):
            if prez_group.user_is_member(request.user) or pro_prez_group.user_is_member(request.user):
                is_president = True

    if is_president:

        registrations = ConferenceRegistration.objects.filter(user__memberprofile__chapter=chapter,
                                                              submitted=True, cancelled=False)
        to_save = []
        delegates = 0
        
        for r in registrations:
            ldd = request.POST.get("ldd_%d" % r.id, '')
            print "getting", "ldd_%d" % r.id, "for", ldd
            if ldd:
                r.ldd_delegate = True
                r.ldd_type = ldd
                r.ldd_chapter = chapter.network
                if request.POST.get("ldd_hotel_%d" % r.id, '') == "on":
                    r.ldd_hotel = True
                else:
                    r.ldd_hotel = False

                delegates = delegates + 1
                to_save.append(r)
                
            elif r.ldd_delegate == True and r.ldd_chapter.id == chapter.id:
                r.ldd_delegate = False
                r.ldd_type = ''
                r.ldd_chapter = None
                r.ldd_hotel = False
                to_save.append(r)
            
        spots, created = LeadershipDaySpots.objects.get_or_create(chapter=chapter)
        print "delegates", delegates, "spots", spots.spots
        if delegates > spots.spots:
            request.user.message_set.create(message='You selected too many delegates - changes were NOT saved!')
        else:
            for s in to_save:
                s.save()
            request.user.message_set.create(message='LDD delegates updated!')

        return HttpResponseRedirect(reverse('conference_list'))

    else:
        return render_to_response('denied.html', context_instance=RequestContext(request))
    
