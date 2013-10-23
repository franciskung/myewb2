# coding=utf-8

"""myEWB conference registration forms

This file is part of myEWB
Copyright 2009 Engineers Without Borders Canada

Created on 2009-10-18
@author Francis Kung
"""

from datetime import date, datetime, time
from decimal import Decimal
from django import forms
from django.contrib.auth.models import User
from django.contrib.formtools.preview import FormPreview
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from emailconfirmation.models import EmailAddress

from communities.models import Community
from conference.constants import *
from conference.models import ConferenceRegistration, ConferenceCode, InvalidCode, ConferenceSession, ROLES_CHOICES
from conference.utils import needsToRenew
from creditcard.models import CC_TYPES, Product
from creditcard.forms import CreditCardNumberField, CreditCardExpiryField, PaymentFormPreview
from profiles.models import MemberProfile
from siteutils.forms import CompactAddressField
from siteutils.models import Address

class ConferenceRegistrationForm(forms.ModelForm):
    theuser = None

    _user = None
    def _get_user(self):
        return self._user
    
    def _set_user(self, value):
        self._user = value
        if self.fields.get('address', None):
            self.fields['address'].user = value
            
    user = property(_get_user, _set_user)

class ConferenceRegistrationProfileForm(ConferenceRegistrationForm):
    first_name = forms.CharField(label='First name')
    last_name = forms.CharField(label='Last name')

    gender = forms.ChoiceField(label='Gender',
                                choices=MemberProfile.GENDER_CHOICES,
                                widget=forms.RadioSelect,
                               )

#    student = forms.BooleanField(label='Are you a student?', required=False)

    language = forms.ChoiceField(label='Language preference',
                                 choices=MemberProfile.LANG_CHOICES,
                                 widget=forms.RadioSelect,
                                 )

    class Meta:
        model = MemberProfile
        fields = ['first_name', 'last_name', 'gender', 'language']


# bleh.  i don't like putting so much UI text here, instead of in a template!!
class ConferenceRegistrationForm1(ConferenceRegistrationForm):
    whoareyou = forms.ChoiceField(label='Who are you?',
                                  choices=WHOAREYOU_CHOICES,
                                  widget=forms.RadioSelect)

    chapter = forms.ChoiceField(label='Your chapter',
                                choices=CHAPTER_CHOICES)
    role= forms.MultipleChoiceField(required=False,
                                     widget=forms.CheckboxSelectMultiple,
                                     choices=ROLES_CHOICES)
    prevConfs = forms.ChoiceField(label='EWB national conferences attended',
								  choices=PASTEVENTS)
    prevRetreats = forms.ChoiceField(label='EWB regional retreats attended',
									 choices=PASTEVENTS)
    cellphone = forms.CharField(label='Your cell phone number',
                                required=False,
                                help_text="(optional) If you wish to receive logistical updates and reminders by text message during the conference")
    class Meta:
        model = ConferenceRegistration
        fields = ['whoareyou', 'chapter', 'role', 'prevConfs', 'prevRetreats', 'cellphone']

class ConferenceRegistrationForm2(ConferenceRegistrationForm):
    nametag = forms.CharField(label='Your name, as it will appear on your nametag')
    nametag_org = forms.CharField(label='Organization, as it will appear on your nametag',
                                  required=False)
    medical = forms.CharField(label='Medications and medical conditions',
                              required=False,
                              widget=forms.Textarea,
                              help_text='If you had a medical emergency, what would you want us to tell paramedics?')
    emergName = forms.CharField(label='Emergency contact: name')
    emergPhone = forms.CharField(label='Emergency contact: phone number')
    emergReln = forms.CharField(label='Emergency contact: relationship')

    childcare = forms.BooleanField(label='I would be interested in group childcare (if it can be arranged)',
                                    required=False)
    childcare_contact = forms.CharField(label='If yes, your contact info (email or phone)',
                                        required=False)
    accessibility = forms.CharField(label='Do you have any accessibility needs?',
                                    widget=forms.Textarea,
                                    required=False)
    headset = forms.BooleanField(label='I would take part in simultaneous translation (if available)',
                                required=False)

    class Meta:
        model = ConferenceRegistration
        fields = ['nametag', 'nametag_org', 'medical', 'emergName', 'emergPhone', 'emergReln', 
                  'childcare', 'childcare_contact',
                  'accessibility', 'headset']

class ConferenceRegistrationForm3(ConferenceRegistrationForm):
    type = forms.ChoiceField(label='Registration type',
                             choices=REGISTRATION_CHOICES,
                             widget=forms.RadioSelect,
                             help_text="""<a href='#' class='confoptiontablelink'>click here for a rate guide and explanation</a>"""
                             )

    code = forms.CharField(label='Registration code',
                           help_text='if you have a registration code, enter it here for a discounted rate.',
                           required=False)

    hotel = forms.ChoiceField(label='Hotel and transportation',
                              choices=HOTEL_CHOICES,
                              widget=forms.RadioSelect,
                              help_text="""<a href='#' class='confoptiontablelink'>click here for a rate guide and explanation</a>"""
                              )
                              
    class Meta:
        model = ConferenceRegistration
        fields = ['type', 'code', 'hotel']

    def clean_code(self):
        codestring = self.cleaned_data['code'].strip().lower()
        
        if not codestring:
            return None
        
        try:
            code = ConferenceCode.objects.get(code=codestring)
                
            if code.isAvailable():
                self.cleaned_data['code'] = code
                return self.cleaned_data['code']
            else:
                raise forms.ValidationError("Registration code has already been used or has expired")
        except ObjectDoesNotExist:
            raise forms.ValidationError("Invalid registration code")
        
    def clean(self):
        if self.cleaned_data.get('type', None) == 'ewb':
            if not self.cleaned_data.get('code', None) and not self._errors.get('code', None):
                self._errors['code'] = ["You must enter a valid registration code"]
                raise forms.ValidationError("Unable to complete registration (see errors below)")
        
        if self.cleaned_data.get('code', None):
            if self.cleaned_data.get('type', None) != 'ewb':
                self._errors['code'] = ["You can only use a registration code with the 'EWB Member' option"]
                raise forms.ValidationError("Unable to complete registration (see errors below)")


        """
        if self.cleaned_data.get('code', None):
            codename = self.cleaned_data['code'].getShortname()
        else:
            codename = "open"
        
        type = self.cleaned_data.get('type', 'nohotel')
        sku = "confreg-2013-" + type + "-" + codename
        
        if not CONF_OPTIONS.get(sku, None):
            self._errors['code'] = ["The registration code you've entered is not valid for the registration type you selected."]
            raise forms.ValidationError("Unable to complete registration (see errors below)")
        """
        return self.cleaned_data
        
class ConferenceRegistrationForm4(ConferenceRegistrationForm):
    hotelgender = forms.ChoiceField(label='Gender preference: I would like to be roomed with',
                                    choices=HOTELGENDER_CHOICES,
                                    widget=forms.RadioSelect)
    hotelsleep = forms.ChoiceField(label='Sleeping preference: I would like to be roomed with',
                                    choices=HOTELSLEEP_CHOICES,
                                    widget=forms.RadioSelect)
    hotelrequests = forms.MultipleChoiceField(label='I would like to be roomed with',
                                            required=False,
                                            widget=forms.CheckboxSelectMultiple,
                                            choices=HOTELREQUESTS_CHOICES)
    hotelroommates = forms.CharField(label='Roommate requests or other clarifications',
                                    widget=forms.Textarea,
                                    help_text='We will do our best to honor roommate requests when they are mutual',
                                    required=False)

    class Meta:
        model = ConferenceRegistration
        fields = ['hotelgender', 'hotelsleep', 'hotelrequests', 'hotelroommates']

class ConferenceRegistrationForm5(ConferenceRegistrationForm):
    foodPrefs = forms.ChoiceField(label='Food preferences',
								  choices=FOOD_CHOICES,
								  widget=forms.RadioSelect)

    dietary = forms.MultipleChoiceField(label='Dietary restrictions',
                                            required=False,
                                            widget=forms.CheckboxSelectMultiple,
                                            choices=DIETARY_CHOICES)
                                            
    specialNeeds = forms.CharField(label='Special needs',
								   required=False,
								   widget=forms.Textarea,
								   help_text="Let us know if there are specific requirements of your diet if your restrictions are not included above. Note: We will do our best to accommodate everyone and will get in touch if we have questions. During the conference if you feel your needs are not being met just let us know and we'll try to adjust.")
    
    bracelet = forms.BooleanField(label='I would like to order a conference bracelet',
                               required=False,
                               help_text="""Cost is $12; provided by <a href="http://www.paperbeadworks.com" target="_new">Paper Bead Works</a> in conference colours""")
    
    handbook = forms.BooleanField(label='I would like a printed copy of the conference delegate handbook',
                               required=False,
                               help_text='A $3 recycling fee applies')
    membership = forms.BooleanField(label='EWB Membership Renewal',
                                           required=False,
                                           help_text='If you are not a paid member of EWB, or if your membership expires before the conference, a membership renewal will be added to your registration.  This membership allows you to vote at the Annual General Meeting.  <strong>If you opt out, you will not be able to vote at the AGM.</strong>')
    
    class Meta:
        model = ConferenceRegistration
        fields = ['foodPrefs', 'dietary', 'specialNeeds', 'bracelet', 'handbook', 'membership']

class ConferenceRegistrationForm6(ConferenceRegistrationForm):
    africaFund = forms.ChoiceField(label='Support an African delegate?',
                                   choices=AFRICA_FUND,
                                   initial='45',
								   required=False)

    africaFundOther = forms.DecimalField(label='If other',
                                         min_value=10.00,
                                         decimal_places=2,
                                         required=False)
    class Meta:
        model = ConferenceRegistration
        fields = ['africaFund']

    def clean_africaFund(self):
        if self.cleaned_data['africaFund']:
            if self.cleaned_data['africaFund'].strip() == '':
                self.cleaned_data['africaFund'] = None
        else:
            self.cleaned_data['africaFund'] = None
                
        return self.cleaned_data['africaFund']
    
    def clean(self):
        if self.cleaned_data['africaFund'] == 'other':
            if not self.cleaned_data.get('africaFundOther', None):
                raise forms.ValidationError("Please enter a value")
            else:
                self.cleaned_data['africaFund'] = self.cleaned_data['africaFundOther']
                
        return self.cleaned_data

class ConferenceRegistrationForm7(ConferenceRegistrationForm):
    leadership_day = forms.BooleanField(label='I would like to apply for Leadership Day',
                                        required=False)
                                        
    class Meta:
        model = ConferenceRegistration
        fields = ['leadership_day']

class ConferenceRegistrationForm8(ConferenceRegistrationForm):
    cc_type = forms.ChoiceField(label='Credit card type',
								  choices=CC_TYPES)
    cc_number = CreditCardNumberField(label='Credit card number')
    cc_expiry = CreditCardExpiryField(label='Credit card expiry',
                                      help_text='MM/YY')
    billing_name = forms.CharField(label='Name on credit card', max_length=255)
    address = CompactAddressField(label='Billing Address')
    id = forms.IntegerField(widget=forms.HiddenInput, required=False)
    
    trnError = None
        
    class Meta:
        model = ConferenceRegistration
        fields = ['cc_type', 'cc_number', 'cc_expiry', 'billing_name', 'address', 'id']
        
#    def __init__(self, *args, **kwargs):
#        super(ConferenceRegistrationForm4, self).__init__(*args, **kwargs)
#        reg = ConferenceRegistration.objects.get(id=cleaned_data['registration_id'])

    def clean(self):
        # If the card is declined at the bank, trnError will get set...
        if self.trnError:
            raise forms.ValidationError("Error: " + self.trnError)
        
        if self.errors:
            return None

        # bypass, since the FormPreview clean isn't on a bound form
        # (but that's ok since we validate the bound version first)
        if self.instance.id:
            reg = self.instance
        elif self.cleaned_data.get('id', None):
            reg = ConferenceRegistration.objects.get(id=self.cleaned_data['id'])
            self.instance = reg
        elif self.cleaned_data.get('id', None):
            reg = ConferenceRegistration.objects.get(id=self.cleaned_data['id'])
            self.instance = reg
        else:
            # this shouldn't happen.
            raise forms.ValidationError("Internal error.  Please email support@my.ewb.ca") 
        
        # and do some auto-processing as needed
        cleaned_data = self.cleaned_data
        cleaned_data['products'] = []
        total_cost = 0
        
        if reg.code:
            regtype = reg.code.getShortname()
        else:
            regtype = reg.type
        
        if not CONF_OPTIONS.get(regtype, None):
            errormsg = "The registration code you've entered is not valid for the registration type you selected."
            raise forms.ValidationError("Unable to complete registration (see errors below)")
         
        cost = CONF_OPTIONS[regtype]['cost']
        name = CONF_OPTIONS[regtype]['name']
        sku = "confreg2014-" + regtype
        product, created = Product.objects.get_or_create(sku=sku)
        if created:
            product.name = name
            product.amount = cost
            product.save()
            
        cleaned_data['products'].append(product.sku)
        total_cost = total_cost + Decimal(product.amount)

        print "membership", reg.membership
        if needsToRenew(self.user.get_profile(), type=reg.type) and reg.membership:
            # FIXME: some duplicated code from profiles.forms (where saving membership fees)
            if self.user.get_profile().student():
                type = "studues"
            else:
                type = "produes"

            chapter = self.user.get_profile().get_chapter()
            if chapter:
                type += "-" + chapter.slug
                chaptername = " (%s)" % chapter.name
            else:
                chaptername = ""
            
            product, created = Product.objects.get_or_create(sku=type)
            if created:
                if self.user.get_profile().student():
                    product.amount = "20.00"
                    product.name = "Student membership" + chaptername
                    product.save()
                else:
                    product.amount = "40.00"
                    product.name = "Professional membership" + chaptername
                    product.save()
            
            cleaned_data['products'].append(product.sku)
            total_cost = total_cost + Decimal(product.amount)

        if reg.africaFund:
            cost = reg.africaFund
            sku = "kumvana2014-%d" % cost
            name = "Support an African delegate ($%d)" % cost
            product, created = Product.objects.get_or_create(sku=sku)
            if created:
                product.name = name
                product.amount = cost
                product.save()
            
            cleaned_data['products'].append(product.sku)
            total_cost = total_cost + Decimal(product.amount)

        if reg.hotel != 'none':
            sku = "confreg2014-%s" % reg.hotel
            name = HOTEL_OPTIONS[reg.hotel]['name']
            cost = HOTEL_OPTIONS[reg.hotel]['cost']
            product, created = Product.objects.get_or_create(sku=sku)
            if created:
                product.name = name
                product.amount = cost
                product.save()
            
            cleaned_data['products'].append(product.sku)
            total_cost = total_cost + Decimal(cost)

        if reg.bracelet:
            sku = "confreg2014-bracelet"
            name = "Conference bracelet"
            product, created = Product.objects.get_or_create(sku=sku)
            if created:
                product.name = name
                product.amount = 12
                product.save()
            
            cleaned_data['products'].append(product.sku)
            total_cost = total_cost + Decimal(12)

        if reg.handbook:
            sku = "confreg2014-handbook"
            name = "Printed handbook"
            product, created = Product.objects.get_or_create(sku=sku)
            if created:
                product.name = name
                product.amount = 3
                product.save()
            
            cleaned_data['products'].append(product.sku)
            total_cost = total_cost + Decimal(3)

        ccard_surcharge = round(total_cost * Decimal('0.025'), 2);
        sku = "ccard-%s" % ccard_surcharge
        name = "Credit card processing fee"
        product, created = Product.objects.get_or_create(sku=sku)
        if created:
            product.name = name
            product.amount = ccard_surcharge
            product.save()
        
        cleaned_data['products'].append(product.sku)
        total_cost = total_cost + Decimal(str(ccard_surcharge))
        reg.ccard_surcharge = Decimal(str(ccard_surcharge))
        reg.save()
        
        
        cleaned_data['total_cost'] = total_cost
        
        cleaned_data['registration_id'] = reg.id
        self.cleaned_data = cleaned_data

        return self.cleaned_data
    
class ConferenceRegistrationFormPreview(PaymentFormPreview):
    preview_template = 'conference/preview.html'
    form_template = 'conference/registration.html'
    username = None
    
    def parse_params(self, *args, **kwargs):
        super(ConferenceRegistrationFormPreview, self).parse_params(*args, **kwargs)
        self.registration_id = kwargs['registration_id']
    
    def done(self, request, cleaned_data):
        # add profile info, as it's needed for CC processing
        #form = self.form(request.POST)
        #reg = self.form.instance
        print "testing the done"
        
        reg = ConferenceRegistration.objects.get(id=cleaned_data['registration_id'])
        form = self.form(request.POST, instance=reg)
        
        if reg.user != request.user:
            # simulate a credit card declined, to trigger form validation failure
            response = (False, "Internal error, please email support@my.ewb.ca")
            
        elif not request.user.email:
            # simulate a credit card declined, to trigger form validation failure
            response = (False, "Please edit your myEWB profile and enter an email address.")

        elif reg.code and reg.code.type != 'i' and not reg.code.isAvailable():
            response = (False, "Registration code has already been used or has expired")
        
        else:
            cleaned_data['email'] = request.user.email
            if request.user.get_profile().default_phone() and request.user.get_profile().default_phone().number:
                cleaned_data['phone'] = request.user.get_profile().default_phone().number
            else:
                cleaned_data['phone'] = '416-481-3696'
            
            # this call sends it to the bank!!
            response = super(ConferenceRegistrationFormPreview, self).done(request, cleaned_data)
            #response = (True, "123", "456")
            
            if not response[0]:
                response = (False, "Credit card: %s" % response[1])
        
        if response[0] == True:
            if reg.code:
                regtype = reg.code.getShortname()
            else:
                regtype = reg.type
            
            reg.submitted = True
            reg.type = regtype
            reg.amountPaid = CONF_OPTIONS[regtype]['cost']
            reg.receiptNum = response[2]
            reg.txid = response[1]
            
            #if cleaned_data.get('grouping', None):
            #    registration.grouping = cleaned_data['grouping']
            
            reg.save()
            
            # and update their membership if they paid it
            if needsToRenew(request.user.get_profile()) and reg.membership:
                request.user.get_profile().pay_membership()
                
            # lastly, add them to the group
            grp, created = Community.objects.get_or_create(slug='conference2014',
                                                           defaults={'invite_only': True,
                                                                     'name': 'National Conference 2014 - EWB delegates',
                                                                     'creator': request.user,
                                                                     'description': 'National Conference 2014 delegates (EWB members)',
                                                                     'mailchimp_name': 'National Conference 2014 members',
                                                                     'mailchimp_category': 'Conference'})

            grp2, created = Community.objects.get_or_create(slug='conference2014-external',
                                                            defaults={'invite_only': True,
                                                                      'name': 'National Conference 2014 - external delegates',
                                                                      'creator': request.user,
                                                                      'description': 'National Conference 2014 delegates (external)',
                                                                      'mailchimp_name': 'National Conference 2014 external',
                                                                      'mailchimp_category': 'Conference'})

            if request.user.is_bulk:
                grp2.add_member(request.user)
            else:
                grp.add_member(request.user)
            
            # don't do the standard render_to_response; instead, do a redirect
            # so that someone can't double-submit by hitting refresh
            return HttpResponseRedirect(reverse('confreg'))
        
        else:
            registration = None
            form.trnError = response[1]
#            form.clean
        needsRenewal = needsToRenew(request.user.get_profile()) and reg.membership

        print "failing.  going to stage 6.  message is %s" % response[1]

        return render_to_response('conference/registration.html',
                                  {'registration': reg,
                                   'form': form,
                                   'stage': '8',
                                   'last_stage': '7',
                                   'user': request.user,
                                   'needsRenewal': needsRenewal
                                  },
                                  context_instance=RequestContext(request)
                                 )

class CodeGenerationForm(forms.Form):
    type = forms.CharField(max_length=1, label='Type of code')
    start = forms.IntegerField(label='Starting at')
    number = forms.IntegerField(label='How many codes')
    

class ConferenceADForm(forms.Form):
    theuser = None

    _user = None
    def _get_user(self):
        return self._user
    
    def _set_user(self, value):
        self._user = value
        if self.fields.get('address', None):
            self.fields['address'].user = value
            
    user = property(_get_user, _set_user)

    africaFund = forms.ChoiceField(label='Support an African delegate?',
                                   choices=AFRICA_FUND,
                                   initial='75',
                                   required=False)

    africaFundOther = forms.DecimalField(label='If other',
                                         min_value=10.00,
                                         decimal_places=2,
                                         required=False)
    
    cc_type = forms.ChoiceField(label='Credit card type',
                                  choices=CC_TYPES)
    cc_number = CreditCardNumberField(label='Credit card number')
    cc_expiry = CreditCardExpiryField(label='Credit card expiry',
                                      help_text='MM/YY')
    billing_name = forms.CharField(label='Name on credit card', max_length=255)
    address = CompactAddressField(label='Billing Address')
    id = forms.IntegerField(widget=forms.HiddenInput, required=False)
    
    trnError = None
    
    def clean_africaFund(self):
        if self.cleaned_data['africaFund']:
            if self.cleaned_data['africaFund'].strip() == '':
                self.cleaned_data['africaFund'] = None
        else:
            self.cleaned_data['africaFund'] = None
            
        if not self.cleaned_data['africaFund']:
            raise forms.ValidationError("Please enter a value")
                
        return self.cleaned_data['africaFund']
    
    def clean(self):
        if self.cleaned_data.get('africaFund', None) == 'other':
            if not self.cleaned_data.get('africaFundOther', None):
                raise forms.ValidationError("Please enter a value")
            else:
                self.cleaned_data['africaFund'] = self.cleaned_data['africaFundOther']
                
        # If the card is declined at the bank, trnError will get set...
        if self.trnError:
            raise forms.ValidationError("Error: " + self.trnError)
        
        if self.errors:
            return None

        # bypass, since the FormPreview clean isn't on a bound form
        # (but that's ok since we validate the bound version first)
        if self.cleaned_data.get('id', None):
            reg = ConferenceRegistration.objects.get(id=self.cleaned_data['id'])
        else:
            # this shouldn't happen.
            raise forms.ValidationError("Internal error.  Please email support@my.ewb.ca") 
        
        # and do some auto-processing as needed
        cleaned_data = self.cleaned_data
        cleaned_data['products'] = []
        total_cost = 0
        
        cost = Decimal(self.cleaned_data['africaFund'])

        sku = "13-africafund-%d" % cost
        name = "Support an African delegate ($%d)" % cost
        product, created = Product.objects.get_or_create(sku=sku)
        if created:
            product.name = name
            product.amount = cost
            product.save()
        
        cleaned_data['products'].append(product.sku)
        total_cost = total_cost + Decimal(product.amount)
        cleaned_data['total_cost'] = total_cost
        
        cleaned_data['registration_id'] = reg.id
        self.cleaned_data = cleaned_data

        return self.cleaned_data
    
    
class ConferenceADFormPreview(PaymentFormPreview):
    preview_template = 'conference/tshirtpreview.html'
    form_template = 'conference/purchase.html'
    username = None
    
    def parse_params(self, *args, **kwargs):
        super(ConferenceADFormPreview, self).parse_params(*args, **kwargs)
        self.registration_id = kwargs['registration_id']
    
    def done(self, request, cleaned_data):
        # add profile info, as it's needed for CC processing
        #form = self.form(request.POST)
        #reg = self.form.instance
        
        reg = ConferenceRegistration.objects.get(id=cleaned_data['registration_id'])
        form = self.form(request.POST)
        
        if reg.user != request.user:
            # simulate a credit card declined, to trigger form validation failure
            response = (False, "Internal error, please email support@my.ewb.ca")
            
        else:
            cleaned_data['email'] = request.user.email
            if request.user.get_profile().default_phone() and request.user.get_profile().default_phone().number:
                cleaned_data['phone'] = request.user.get_profile().default_phone().number
            else:
                cleaned_data['phone'] = '416-481-3696'
            
            # this call sends it to the bank!!
            response = super(ConferenceADFormPreview, self).done(request, cleaned_data)
            
            if not response[0]:
                response = (False, "Credit card: %s" % response[1])
        
        if response[0] == True:
            africaFund = reg.africaFund
            if not africaFund:
                africaFund = 0
            reg.africaFund = africaFund + Decimal(cleaned_data['africaFund'])
            reg.save()
            
            # don't do the standard render_to_response; instead, do a redirect
            # so that someone can't double-submit by hitting refresh
            request.user.message_set.create(message='African Delegate contribution received!')
            return HttpResponseRedirect(reverse('confreg'))
        
        else:
            registration = None
            form.trnError = response[1]
            form.clean

        return render_to_response('conference/purchase.html',
                                  {'registration': registration,
                                   'form': form,
                                   'user': request.user,
                                  },
                                  context_instance=RequestContext(request)
                                 )

class ConferenceSkiForm(forms.Form):
    theuser = None

    _user = None
    def _get_user(self):
        return self._user
    
    def _set_user(self, value):
        self._user = value
        if self.fields.get('address', None):
            self.fields['address'].user = value
            
    user = property(_get_user, _set_user)

#    ski = forms.ChoiceField(label='Bring a guest to the gala?',
#                               choices=SKI_CHOICES)
    
    cc_type = forms.ChoiceField(label='Credit card type',
                                  choices=CC_TYPES)
    cc_number = CreditCardNumberField(label='Credit card number')
    cc_expiry = CreditCardExpiryField(label='Credit card expiry',
                                      help_text='MM/YY')
    billing_name = forms.CharField(label='Name on credit card', max_length=255)
    address = CompactAddressField(label='Billing Address')
    id = forms.IntegerField(widget=forms.HiddenInput, required=False)
    
    trnError = None
    
    def clean(self):
        # If the card is declined at the bank, trnError will get set...
        if self.trnError:
            raise forms.ValidationError("Error: " + self.trnError)
        
        if self.errors:
            return None

        # bypass, since the FormPreview clean isn't on a bound form
        # (but that's ok since we validate the bound version first)
        if self.cleaned_data.get('id', None):
            reg = ConferenceRegistration.objects.get(id=self.cleaned_data['id'])
        else:
            # this shouldn't happen.
            raise forms.ValidationError("Internal error.  Please email support@my.ewb.ca") 
        
        # and do some auto-processing as needed
        cleaned_data = self.cleaned_data
        cleaned_data['products'] = []
        total_cost = 0

#        if cleaned_data['ski'] == 's':        
#            sku = "12-conf-ski-student"
#            name = "Conference ski trip (student)"
#            cost = 48
#        else:
#            sku = "12-conf-ski-adult"
#            name = "Conference ski trip (adult)"
#            cost = 60
        sku = "13-conf-galaguest"
        name = "Extra Gala ticket"
        product, created = Product.objects.get_or_create(sku=sku)
        if created:
            product.name = name
            product.amount = 75
            product.save()
            
        cleaned_data['products'].append(product.sku)
        total_cost = total_cost + Decimal(product.amount)
        cleaned_data['total_cost'] = total_cost
        
        cleaned_data['registration_id'] = reg.id
        self.cleaned_data = cleaned_data

        return self.cleaned_data
    
    
class ConferenceSkiFormPreview(PaymentFormPreview):
    preview_template = 'conference/tshirtpreview.html'
    form_template = 'conference/purchase.html'
    username = None
    
    def parse_params(self, *args, **kwargs):
        super(ConferenceSkiFormPreview, self).parse_params(*args, **kwargs)
        self.registration_id = kwargs['registration_id']
    
    def done(self, request, cleaned_data):
        # add profile info, as it's needed for CC processing
        #form = self.form(request.POST)
        #reg = self.form.instance
        
        reg = ConferenceRegistration.objects.get(id=cleaned_data['registration_id'])
        form = self.form(request.POST)
        
        if reg.user != request.user:
            # simulate a credit card declined, to trigger form validation failure
            response = (False, "Internal error, please email support@my.ewb.ca")
            
        else:
            cleaned_data['email'] = request.user.email
            if request.user.get_profile().default_phone() and request.user.get_profile().default_phone().number:
                cleaned_data['phone'] = request.user.get_profile().default_phone().number
            else:
                cleaned_data['phone'] = '416-481-3696'
            
            # this call sends it to the bank!!
            response = super(ConferenceSkiFormPreview, self).done(request, cleaned_data)
            
            if not response[0]:
                response = (False, "Credit card: %s" % response[1])
        
        if response[0] == True:
            reg.extra_gala = True      # somethin like this...
            reg.save()
            
            # don't do the standard render_to_response; instead, do a redirect
            # so that someone can't double-submit by hitting refresh
            request.user.message_set.create(message='Ski trip order received!')
            return HttpResponseRedirect(reverse('confreg'))
        
        else:
            registration = None
            form.trnError = response[1]
            form.clean

        return render_to_response('conference/purchase.html',
                                  {'registration': registration,
                                   'form': form,
                                   'user': request.user,
                                  },
                                  context_instance=RequestContext(request)
                                 )

class ConferenceResumeForm(forms.Form):
    resume = forms.FileField(label='Resume',
                             required=True,
                             help_text="Your resume (to share with our sponsors)")
    
    
class ConferenceSignupForm(forms.Form):

    firstname = forms.CharField(label="First name")
    lastname = forms.CharField(label="Last name")
    email = forms.EmailField(label = "Email", required = True, widget = forms.TextInput())
    gender = forms.ChoiceField(choices=MemberProfile.GENDER_CHOICES,
                               widget=forms.RadioSelect,
                               required=True)
    language = forms.ChoiceField(label="Preferred language",
                                 choices=MemberProfile.LANG_CHOICES,
                                 widget=forms.RadioSelect,
                                 required=True)
    
    def clean_email(self):
        other_emails = EmailAddress.objects.filter(email__iexact=self.cleaned_data['email'])
        verified_emails = other_emails.filter(verified=True, user__is_bulk=False)
        if verified_emails.count() > 0:
            raise forms.ValidationError("This email address has already been used. Please sign in or use a different email.")
        
        # this is probably redundant, but just to be sure...
        users = User.objects.filter(email=self.cleaned_data['email'], is_bulk=False)
        if users.count():
            raise forms.ValidationError("This email address has already been used. Please sign in or use a different email.")
        
        return self.cleaned_data['email']

    def save(self):
        firstname = self.cleaned_data['firstname']
        lastname = self.cleaned_data['lastname']
        email = self.cleaned_data["email"]
        
        try:
            new_user = User.objects.get(email=email, is_bulk=1)
        except User.DoesNotExist:
            new_user = User.extras.create_bulk_user(email, verified=True)
            
        profile = new_user.get_profile()
        profile.first_name = firstname
        profile.last_name = lastname
        profile.gender = self.cleaned_data['gender']
        profile.language = self.cleaned_data['language']
        profile.save()
        
        new_user.first_name = firstname
        new_user.last_name = lastname
        password = User.objects.make_random_password()
        new_user.set_password(password)
        new_user.save()
        
        return new_user.username, password # required for authenticate()

CONFERENCE_TIMES = (('8', '8'),
                    ('9', '9'),
                    ('10', '10'),
                    ('11', '11'),
                    ('12', '12'),
                    ('13', '13'),
                    ('14', '14'),
                    ('15', '15'),
                    ('16', '16'),
                    ('17', '17'),
                    ('18', '18'),
                    ('19', '19'),
                    ('20', '20'),
                    ('21', '21'))
CONFERENCE_MINUTES = ((':00', ':00'),
                      (':30', ':30'))
class DropdownTimeWidget(forms.MultiWidget):
    def __init__(self, widgets=None, attrs=None):
        if not widgets:
            widgets = (forms.Select(choices=CONFERENCE_TIMES),
                       forms.Select(choices=CONFERENCE_MINUTES))
            
        super(DropdownTimeWidget, self).__init__(widgets, attrs)
     
    def decompress(self, value):
        if value:
            return [value.hour, ":%02d" % value.minute]
        return [None, None]

class DropdownTimeField(forms.MultiValueField):
    widget = DropdownTimeWidget

    def __init__(self, fields=None, *args, **kwargs):
        if not fields:
            fields=(forms.ChoiceField(choices=CONFERENCE_TIMES),
                    forms.ChoiceField(choices=CONFERENCE_MINUTES))
            
        super(DropdownTimeField, self).__init__(fields, *args, **kwargs)        
    
    def compress(self, data_list):
        if data_list:
            hour = int(data_list[0])
            min = int(data_list[1][1:])
            return time(hour, min)    

CONFERENCE_DAY_CHOICES = (('2011-01-13', 'Thursday'),
                          ('2011-01-14', 'Friday'),
                          ('2011-01-15', 'Saturday'))
CONFERENCE_LENGTH_CHOICES = (('30', '0 hours, 30 minutes'),
                             ('60', '1 hour'),
                             ('90', '1 hour, 30 minutes'),
                             ('120', '2 hours'),
                             ('150', '2 hours, 30 minutes'),
                             ('180', '3 hours'),
                             ('210', '3 hours, 30 minutes'),
                             ('240', '4 hours'),
                             ('270', '4 hours, 30 minutes'),
                             ('300', '5 hours'),
                             ('330', '5 hours, 30 minutes'),
                             ('360', '6 hours'),
                             ('390', '6 hours, 30 minutes'),
                             ('420', '7 hours'),
                             ('450', '7 hours, 30 minutes'),
                             ('480', '8 hours'),
                             )
class ConferenceSessionForm(forms.ModelForm):
    #day = forms.ChoiceField(choices=CONFERENCE_DAY_CHOICES)
    #time = DropdownTimeField()
    #length = forms.ChoiceField(choices=CONFERENCE_LENGTH_CHOICES)
    
    class Meta:
        model = ConferenceSession
        #fields = ['name', 'room', 'day', 'time', 'length',
        #          'stream', 'capacity',
        #          'short_description', 'long_description']
        fields = ['name', 'name_fr', 'room', 'capacity',
                  'description', 'description_fr', 'prep', 'prep_fr']

SMS_CHOICES = (('all', 'All conference delegates'),
#               ('internal', 'Internal (EWB member + alumni) delegates'),
#               ('external', 'External delegates'),
               ('alumni', 'Alumni delegates'),
               ('hotel', 'Delegates with a hotel room'),
#               ('nohotel', 'Internal delegates without a hotel room (incl alumni)'),
#               ('nohotel-all', 'All delegates without a hotel room (internal and external)'))
               ('nohotel', 'All delegates without a hotel room'))
class ConferenceSmsForm(forms.Form):
    grouping = forms.ChoiceField(choices=SMS_CHOICES,
                                 widget=forms.RadioSelect,
                                 required=True)
    message = forms.CharField(max_length=160,
                              widget=forms.Textarea,
                              help_text='Maximum 160 characters.')


