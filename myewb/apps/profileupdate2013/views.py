from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext, Context, loader
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from pinax.apps.account.forms import AddEmailForm

from emailconfirmation.models import EmailAddress, EmailConfirmation

from interests.models import Interest
from profiles.forms import AddressForm, AddressFormFR, PhoneNumberForm, PhoneNumberFormFR, \
                           StudentRecordForm, StudentRecordFormFR, WorkRecordForm, WorkRecordFormFR
#                            StudentRecordForm, WorkRecordForm
from profiles.models import MemberProfile
from siteutils.models import Address, PhoneNumber
from datetime import datetime
from profileupdate2013.models import ProfileUpdate, ProfileUpdateForm, ProfileUpdateFormFR

@login_required
def intro(request):
    profile_update = ProfileUpdate.objects.create(user=request.user,
                                                  profile=request.user.get_profile())
                                                  
    request.session['profileupdate'] = profile_update

    return render_to_response("profileupdate2013/intro.html",
                              {'profile_user': request.user},
                              context_instance=RequestContext(request))

@login_required
def contact(request):
    profile = request.user.get_profile()

    if request.GET.get('lang', 'english') == 'fr':
        request.session['profilelang'] = 'fr'
        request.session['django_language'] = 'fr_FR'
        address_form = AddressFormFR()
        phone_form = PhoneNumberFormFR()
    else:
        request.session['profilelang'] = 'en'
        request.session['django_language'] = 'en_US'
        address_form = AddressForm()
        phone_form = PhoneNumberForm()
    
    add_email_form = AddEmailForm(user=request.user)

    profile_update = request.session.get('profileupdate')
    if profile_update:
        profile_update = ProfileUpdate.objects.get(id=profile_update.id)
    else:
        profile_update = ProfileUpdate.objects.create(user=request.user,
                                                      profile=request.user.get_profile())
        request.session['profileupdate'] = profile_update
    profile_update.contact = datetime.now()
    profile_update.save()

    if request.method == 'POST':
        
        action = request.POST.get('action', None)
        
        if action == 'email_primary':
            email_id = request.POST.get('email', None)
            if email_id:
                email = EmailAddress.objects.get(id=email_id, user=request.user)
                email.set_as_primary()
                
        elif action == 'email_resend':
            email_id = request.POST.get('email', None)
            if email_id:
                email = EmailAddress.objects.get(id=email_id, user=request.user)
                if not email.verified:
                    EmailConfirmation.objects.send_confirmation(email)

        elif action == 'email_remove':
            email_id = request.POST.get('email', None)
            if email_id:
                email = EmailAddress.objects.get(id=email_id, user=request.user)
                email.delete()

        elif action == 'email_new':
            add_email_form = AddEmailForm(request.user, request.POST)
            if add_email_form.is_valid():
                add_email_form.save()
            
        elif action == 'address_primary':
            address_id = request.POST.get('address', None)
            if address_id:
                address = Address.objects.get(id=address_id, memberprofile=profile)
                profile.addresses_primary = address
                profile.save()
                
        elif action == 'address_remove':
            address_id = request.POST.get('address', None)
            if address_id:
                address = Address.objects.get(id=address_id, memberprofile=profile)
                profiles = MemberProfile.objects.filter(addresses_primary=address)
                for p in profiles:
                    p.addresses_primary = None
                    p.save()
                profile.addresses_primary = None
                address.delete()
                
        elif action == 'address_new':
            address_form = AddressForm(request.POST)
            if address_form.is_valid():
                address = address_form.save(commit=False)
                address.content_object = profile
                address.save()
                profile.addresses.add(address)
                profile.addresses_primary = address
                profile.save()
            
        elif action == 'phone_primary':
            phone_id = request.POST.get('phone', None)
            if phone_id:
                phone = PhoneNumber.objects.get(id=phone_id, memberprofile=profile)
                profile.phone_numbers_primary = phone
                profile.save()
                
        elif action == 'phone_remove':
            phone_id = request.POST.get('phone', None)
            if phone_id:
                phone = PhoneNumber.objects.get(id=phone_id, memberprofile=profile)
                profiles = MemberProfile.objects.filter(phone_numbers_primary=phone)
                for p in profiles:
                    p.phone_numbers_primary = None
                    p.save()
                profile.phone_numbers_primary = None
                phone.delete()
                
        elif action == 'phone_new':
            phone_form = PhoneNumberForm(request.POST)
            if phone_form.is_valid():
                phone = phone_form.save(commit=False)
                phone.content_object = profile
                phone.save()
                profile.phone_numbers.add(phone)
                profile.phone_numbers_primary = phone
                profile.save()

    primary_email = request.user.emailaddress_set.filter(primary=True)
    if primary_email.count():
        primary_email = primary_email[0]
    else:
        primary_email = None
        
    additional_emails = request.user.emailaddress_set.filter(primary=False)
    if profile.addresses.count() and not profile.addresses_primary:
        addr = profile.addresses.order_by('-last_updated')
        profile.addresses_primary = addr[0]
        profile.save()
        
    if profile.phone_numbers.count() and not profile.phone_numbers_primary:
        ph = profile.phone_numbers.order_by('-last_updated')
        profile.phone_numbers_primary = ph[0]
        profile.save()
        

    if request.session.get('profilelang', 'en') == 'fr':
        template = "profileupdate2013/contact_fr.html"
    else:
        template = "profileupdate2013/contact.html"

    return render_to_response(template,
                              {'profile_user': request.user,
                               'primary_email': primary_email,
                               'additional_emails': additional_emails,
                               'add_email_form': add_email_form,
                               'address_form': address_form,
                               'phone_form': phone_form},
                              context_instance=RequestContext(request))

@login_required
def workplace(request):
    profile = request.user.get_profile()

    if request.session.get('profilelang', 'en') == 'fr':
        workplace_form = WorkRecordFormFR()
        school_form = StudentRecordFormFR()
    else:
        workplace_form = WorkRecordForm()
        school_form = StudentRecordForm()

    profile_update = request.session.get('profileupdate')
    if profile_update:
        profile_update = ProfileUpdate.objects.get(id=profile_update.id)
    else:
        profile_update = ProfileUpdate.objects.create(user=request.user,
                                                      profile=request.user.get_profile())
        request.session['profileupdate'] = profile_update
    profile_update.workplace = datetime.now()
    profile_update.save()

    if request.method == 'POST':
        
        action = request.POST.get('action', None)
        
        if action == 'workplace':
            if request.session.get('profilelang', 'en') == 'fr':
                workplace_form = WorkRecordFormFR(request.POST)
            else:
                workplace_form = WorkRecordForm(request.POST)
            if workplace_form.is_valid():
                workplace = workplace_form.save(commit=False)
                workplace.user = request.user
                workplace.save()
        
        elif action == 'school':
            if request.session.get('profilelang', 'en') == 'fr':
                school_form = StudentRecordFormFR(request.POST)
            else:
                school_form = StudentRecordForm(request.POST)
            if school_form.is_valid():
                school = school_form.save(commit=False)
                school.user = request.user
                school.save()

    if request.session.get('profilelang', 'en') == 'fr':
        template = "profileupdate2013/workplace_fr.html"
    else:
        template = "profileupdate2013/workplace.html"

    return render_to_response(template,
                              {'profile_user': request.user,
                               'is_me': True,
                               'workplace_form': workplace_form,
                               'school_form': school_form},
                              context_instance=RequestContext(request))

@login_required
def demographics(request):
    profile = request.user.get_profile()

    if request.session.get('profilelang', 'en') == 'fr':
        update_form = ProfileUpdateFormFR()
    else:
        update_form = ProfileUpdateForm()
    
    profile_update = request.session.get('profileupdate')
    if profile_update:
        profile_update = ProfileUpdate.objects.get(id=profile_update.id)
    else:
        profile_update = ProfileUpdate.objects.create(user=request.user,
                                                      profile=request.user.get_profile())
        request.session['profileupdate'] = profile_update
    profile_update.demographics = datetime.now()
    profile_update.save()

    if request.method == 'POST':
        if request.session.get('profilelang', 'en') == 'fr':
            update_form = ProfileUpdateFormFR(request.POST, instance=profile_update)
        else:
            update_form = ProfileUpdateForm(request.POST, instance=profile_update)
        
        if update_form.is_valid():
            profile_update = update_form.save()
        
            return HttpResponseRedirect(reverse('profileupdate_interests'))
    
    if request.session.get('profilelang', 'en') == 'fr':
        template = "profileupdate2013/demographics_fr.html"
    else:
        template = "profileupdate2013/demographics.html"

    return render_to_response(template,
                              {'profile_user': request.user,
                               'form': update_form},
                              context_instance=RequestContext(request))


@login_required
def interests(request):
    interests = Interest.objects.filter(highlighted=True)
    profile = request.user.get_profile()
    
    profile_update = request.session.get('profileupdate')
    if profile_update:
        profile_update = ProfileUpdate.objects.get(id=profile_update.id)
    else:
        profile_update = ProfileUpdate.objects.create(user=request.user,

                                                      profile=request.user.get_profile())
        request.session['profileupdate'] = profile_update
    profile_update.interests = datetime.now()
    profile_update.save()

    if request.method == 'POST':
        for i in interests:
            if request.POST.get("interest_%d" % i.id, None):
                i.users.add(profile)
                
                
        extra = request.POST.get('extra', None)
        if extra:
            extra = extra.strip()
        if extra:
            for i in extra.split("\n"):
                i = i.strip()
                if i:
                    interest, created = Interest.objects.get_or_create(tag=i)
                    interest.users.add(profile)
                    
        return HttpResponseRedirect(reverse('profileupdate_complete'))

    if request.session.get('profilelang', 'en') == 'fr':
        template = "profileupdate2013/interests_fr.html"
    else:
        template = "profileupdate2013/interests.html"

    return render_to_response(template,
                              {'profile_user': request.user,
                               'interests': interests},
                              context_instance=RequestContext(request))

@login_required
def complete(request):
    return render_to_response("profileupdate2013/complete.html",
                              {'profile_user': request.user},
                              context_instance=RequestContext(request))

