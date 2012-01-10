"""myEWB conference SMS noties

This file is part of myEWB
Copyright 2009-2010 Engineers Without Borders Canada

@author: Francis Kung
"""

import settings
from datetime import date, datetime

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponseForbidden, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.template.loader import render_to_string

from threading import Thread
from twilio import twilio
from mailer import send_mail

from conference.forms import ConferenceSmsForm, SMS_CHOICES
from conference.models import ConferenceRegistration, ConferenceSession, ConferenceCellNumber, ConferencePhoneFrom
from siteutils.shortcuts import get_object_or_none

CONFERENCE_DAYS = (('thurs', 'Thursday', 13),
                   ('fri', 'Friday', 14),
                   ('sat', 'Saturday', 15))

def do_send_sms(args):
    api = settings.TWILIO_API_VERSION
    sid = settings.TWILIO_ACCOUNT_SID
    token = settings.TWILIO_ACCOUNT_TOKEN

    account = twilio.Account(sid, token)

    for x in args:
        try:
            response = account.request('/%s/Accounts/%s/SMS/Messages' % (api, sid),
                                       'POST', x)
            #print x['To']
        except Exception, e:
            response = e.read()

            send_mail(subject="sms error",
                      txtMessage="%s \n From: %s \n To: %s \n" % (response, x['From'], x['To']),
                      htmlMessage=None,
                      fromemail="itsupport@ewb.ca",
                      recipients=['franciskung@ewb.ca',],
                      use_template=False)

        break


@login_required
def send_sms(request, session=None):
    if not request.user.has_module_perms("conference"):
        return HttpResponseRedirect(reverse('conference_schedule'))
    
    s = get_object_or_none(ConferenceSession, id=session)
    response = None

    if request.method == 'POST':
        api = settings.TWILIO_API_VERSION
        sid = settings.TWILIO_ACCOUNT_SID
        token = settings.TWILIO_ACCOUNT_TOKEN
        number = settings.TWILIO_PHONE_NUMBER
        
        form = ConferenceSmsForm(request.POST)
        
        if s:
            del(form.fields['grouping'])

        if form.is_valid():
            success = 0
            failed = 0
            
            registrations = []
            if s:
                registrations = ConferenceRegistration.objects.filter(user__in=list(s.attendees.all()))
            elif form.cleaned_data['grouping'] == 'all':
                registrations = ConferenceRegistration.objects.all()

            #elif form.cleaned_data['grouping'] == 'internal':
            #    registrations = ConferenceRegistration.objects.filter(~Q(type__contains='day'))
            #elif form.cleaned_data['grouping'] == 'external':
            #    registrations = ConferenceRegistration.objects.filter(type__contains='day')

            elif form.cleaned_data['grouping'] == 'alumni':
                registrations = ConferenceRegistration.objects.filter(type__contains='alumni')
            elif form.cleaned_data['grouping'] == 'hotel':
                registrations = ConferenceRegistration.objects.filter(Q(type__contains='single') | Q(type__contains='double') | Q(type__contains='quad'))
            elif form.cleaned_data['grouping'] == 'nohotel':
                registrations = ConferenceRegistration.objects.filter(Q(type__contains='nohotel'))
            #elif form.cleaned_data['grouping'] == 'nohotel-all':
            #    registrations = ConferenceRegistration.objects.filter(~Q(type__contains='single'), ~Q(type__contains='double'))
            
            registrations = registrations.filter(cancelled=False, submitted=True, cellphone__isnull=False, cellphone_optout__isnull=True)

            # just for debugging...
            #registrations = registrations.filter(cellphone='mynumber')
            
            #if not s and form.cleaned_data['grouping'] == 'all':
            #    registrations = list(registrations)
            #    registrations.extend(list(ConferenceCellNumber.objects.filter(cellphone_optout__isnull=True)))
            
            # Twilio
            account = twilio.Account(sid, token)
            #thread_list = {}
            batch_messages = []
            for r in registrations:
                if r.cellphone_optout or not r.cellphone:
                    continue

                """
                fromnumber = r.cellphone_from
                if not fromnumber:
                    numbers = ConferencePhoneFrom.objects.order_by('accounts')
                    fromnumber = numbers[0]
                    r.cellphone_from=fromnumber
                    r.save()
                    fromnumber.accounts = fromnumber.accounts + 1
                    fromnumber.save() 
                        
                d = {'From': fromnumber.number,   #  '415-599-2671',
                     'To': r.cellphone,
                     'Body': form.cleaned_data['message']}
                
                if fromnumber.number not in thread_list:
                    thread_list[fromnumber.number] = []
                thread_list[fromnumber.number].append(d)
                
            try:
                for i in thread_list:
                    t = Thread(target=do_send_sms, args=(thread_list[i],))
                    t.start()
                
            except Exception, e:
                #response = e.read()
                failed = failed + 1
            else:
                success = success + 1
                """

                d = {'From': number,
                     'To': r.cellphone,
                     'Body': form.cleaned_data['message']}

                batch_messages.append(d)                
                
            try:
                t = Thread(target=do_send_sms, args=(batch_messages,))
                t.start()
                
            except Exception, e:
                #response = e.read()
                failed = failed + 1
            else:
                success = success + 1

            response = ""
            if failed:
                response = "%s<br/>%d messages queued for sending, but some errors encountered =(" % (response, len(batch_messages))
            else:
                response = "%s<br/>%d messages queued for sending!" % (response, len(batch_messages))
            
    else:
        form = ConferenceSmsForm()
        if s:
            del(form.fields['grouping'])
            
    context = {}
    if s:
        context['session'] = s
    if response:
        context['response'] = response
    else:
        context['form'] = form
        
    return render_to_response("conference/schedule2/sms.html",
                              context,
                              context_instance = RequestContext(request))

# This requires mailbox support; see sms_poll.php and put it on a cron =)
def stop_sms(request):
    """
    Twilio format.  So much easier.
    """
    if request.method != 'POST' or not request.POST.get('From', None) or not request.POST.get('Body', None):
        return HttpResponse("not supported")

    tonumber = request.POST.get('To', None)
    fromnumber = request.POST.get('From', None)
    txtmessage = request.POST.get('Body', None)
    result = ""
    
    if fromnumber[0:1] == '1':
        fromnumber = fromnumber[1:]
    elif fromnumber[0:2] == '+1':
        fromnumber = fromnumber[2:]
        
    if tonumber[0:1] == '1':
        tonumber = tonumber[1:]
    elif tonumber[0:2] == '+1':
        tonumber = tonumber[2:]

#    if fromnumber == '5193627821' or tonumber == '5193627821':
#        return HttpResponse("")
        
    txtmessage = txtmessage.strip().lower()
    
    if txtmessage.find('stop') != -1:
        result = result + "stopping\n"
        r = ConferenceRegistration.objects.filter(cellphone=fromnumber, cancelled=False, submitted=True)
        
        if fromnumber and r.count():
            for reg in r:
                result = result + "goodbye %s\n" % reg.user.email
                reg.cellphone_optout = datetime.now()
                reg.save()
                #provider = reg.cellphone_from
                #if provider:
                #    provider.accounts = provider.accounts - 1
                #    provider.save()

        """                
        numbers = ConferenceCellNumber.objects.filter(cellphone=fromnumber, cellphone_optout__isnull=True)
        if fromnumber and numbers.count():
            for n in numbers:
                n.cellphone_optout = datetime.now()
                n.save()
                provider = n.cellphone_from
                if provider:
                    provider.accounts = provider.accounts - 1
                    provider.save()
        """
                    
        xmlresponse = """<?xml version="1.0" encoding="UTF-8" ?>
<Response>
    <Sms>You have been unsubscribed.  To re-subscribe to EWB National Conference 2011 notices, reply with START</Sms>
</Response>
"""
        return HttpResponse(xmlresponse)
            
                
    elif txtmessage.find('start') != -1:
    #else:
        r = ConferenceRegistration.objects.filter(cellphone=fromnumber, cancelled=False)
        numbers = ConferenceCellNumber.objects.filter(cellphone=fromnumber)

        if r.count():
            reg = r[0]
            reg.cellphone_optout = None
            reg.save()

            xmlresponse = """<?xml version="1.0" encoding="UTF-8" ?>
<Response>
    <Sms>Welcome to the EWB National Conference 2011 notices list.  To unsubscribe, reply with STOP</Sms>
</Response>
"""
            return HttpResponse(xmlresponse)
    
            """            
            if reg.cellphone_from:
                provider = reg.cellphone_from
            else:
                provider, created = ConferencePhoneFrom.objects.get_or_create(number=tonumber)
                reg.cellphone_from = provider
                reg.save()
            provider.accounts = provider.accounts + 1
            provider.save()
            """

        """
        elif numbers.count():
            result = result + "already found %s\n" % fromnumber
            n = numbers[0]
            n.cellphone_optout = None
            n.save()
            
            if n.cellphone_from:
                provider = n.cellphone_from
            else:
                provider, created = ConferencePhoneFrom.objects.get_or_create(number=tonumber)
                n.cellphone_from = provider
                n.save()
            provider.accounts = provider.accounts + 1
            provider.save()
                
        else:
            provider, created = ConferencePhoneFrom.objects.get_or_create(number=tonumber)
            ConferenceCellNumber.objects.create(cellphone=fromnumber, cellphone_from=provider)
            result = result + "adding %s\n" % fromnumber
        """
    
#        xmlresponse = """<?xml version="1.0" encoding="UTF-8" ?>
#<Response>
#    <Sms>Welcome to the EWB National Conference 2011 notices list.  To unsubscribe, reply with STOP</Sms>
#</Response>
#"""
#        return HttpResponse(xmlresponse)
    
    #else:
    #    result = result + "dunno what to do\n"
    #    result = result + txtmessage
    else:
        return HttpResponse("")

        
    return HttpResponse(result)
    
