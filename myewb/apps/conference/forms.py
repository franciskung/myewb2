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
from conference.models import ConferenceRegistration, ConferenceCode, AlumniConferenceCode, QuasiVIPCode, FriendsConferenceCode, InvalidCode, ConferenceSession, ConferenceQuestionnaire, ROLES_CHOICES
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
            
        #
        #if value.is_bulk:
        #    del(self.fields['prevConfs'])
        #    del(self.fields['prevRetreats'])
        #    #del(self.fields['code'])
        #    self.fields['type'].choices=EXTERNAL_CHOICES
        #else:
        #    del(self.fields['grouping'])
        #    del(self.fields['grouping2'])
            
    user = property(_get_user, _set_user)

class ConferenceRegistrationProfileForm(ConferenceRegistrationForm):
    first_name = forms.CharField(label='First name')
    last_name = forms.CharField(label='Last name')

    gender = forms.ChoiceField(label='Gender',
#                               choices=(('', ''),
#                                         ('M', 'Male'),
#                                         ('F', 'Female')),
                                choices=MemberProfile.GENDER_CHOICES,
                                widget=forms.RadioSelect,
                               )

#    student = forms.BooleanField(label='Are you a student?', required=False)

    language = forms.ChoiceField(label='Language preference',
#                                 choices=(('', ''),
#                                          ('E', 'English'),
#                                          ('F', 'Francais')),
                                 choices=MemberProfile.LANG_CHOICES,
                                 widget=forms.RadioSelect,
                                 )

#    date = forms.DateTimeField(widget=forms.HiddenInput)

    class Meta:
        model = MemberProfile
        fields = ['first_name', 'last_name', 'gender', 'language']


class ConferenceRegistrationForm1(ConferenceRegistrationForm):
    # bleh.  i don't like putting so much UI text here, instead of in a template!!


    code = forms.CharField(label='Registration code',
                           help_text='if you have a registration code, enter it here for a discounted rate.',
                           required=False)
    type = forms.ChoiceField(label='Registration type',
                             #choices=FINAL_CHOICES,
                             choices=ROOM_CHOICES,
                             widget=forms.RadioSelect,
                             initial='nohotel',
                             help_text="""Hotel options are only available with use of a registration code.<br/><a href='#' id='confoptiontablelink'>click here for a rate guide and explanation</a>"""
                             #help_text="""Note that tickets to the Gala on Saturday evening featuring K'naan are sold separately, through the Gala event site"""
                             )
    
    roommate = forms.CharField(label='Roommate request<br/>(with a hotel option, if any)', required=False,
                               help_text='Requests are not guaranteed; however if all roommates list each other it will increase your chances.<br/>Rooms are all-male or all-female (no co-ed rooms).')

    extra_gala = forms.BooleanField(label='Add an extra gala ticket ($75)',
                                    required=False,
                                    help_text='Would you like to bring a guest to the closing gala, who is not registered for conference')

    class Meta:
        model = ConferenceRegistration
#        fields = ['headset', 'foodPrefs', 'specialNeeds', 'emergName', 'emergPhone',
#                  'cellphone', 'code', 'type', 'roommate', 'tshirt']
        fields = ['code', 'type', 'roommate', 'extra_gala']

    def clean_code(self):
        codestring = self.cleaned_data['code'].strip().lower()
        
        if not codestring:
            return None
        
        try:
            if codestring == 'ewbalumni':
                code, created = AlumniConferenceCode.objects.get_or_create(type='i', number=1)
            #elif (codestring == 'ewbconfspecial'):
            #    code = QuasiVIPCode()
            #elif (codestring == 'ewbfriendsconf'):
            #    code = FriendsConferenceCode()
            else:
                code = ConferenceCode.objects.get(code=codestring)
                
            if code.isAvailable():
                self.cleaned_data['code'] = code
                return self.cleaned_data['code']
            else:
                raise forms.ValidationError("Registration code has already been used or has expired")
        except ObjectDoesNotExist:
            raise forms.ValidationError("Invalid registration code")
        
    def clean(self):
#        if not self.user.first_name \
#            or not self.user.last_name \
#            or not self.user.get_profile().gender \
#            or not self.user.email:
#            
#            raise forms.ValidationError("Please fill out your full myEWB profile, including full name, email, and gender")
        
        if self.cleaned_data.get('code', None):
            codename = self.cleaned_data['code'].getShortname()
        else:
            codename = "open"
        
        type = self.cleaned_data.get('type', 'nohotel')
        sku = "confreg-2013-" + type + "-" + codename
        
        if not CONF_OPTIONS.get(sku, None):
            self._errors['code'] = ["The registration code you've entered is not valid for the registration type you selected."]
            raise forms.ValidationError("Unable to complete registration (see errors below)")
         
        return self.cleaned_data
        
class ConferenceRegistrationForm2(ConferenceRegistrationForm):
    foodPrefs = forms.ChoiceField(label='Food preferences',
								  choices=FOOD_CHOICES,
								  widget=forms.RadioSelect,
								  initial='vegetarian',
								  help_text='Please use the text area below to provide details or any other requirements, if needed')

    specialNeeds = forms.CharField(label='Special needs',
								   required=False,
								   widget=forms.Textarea,
								   help_text='Please let us know about any special dietary, accessibility or other needs you may have, or any medical conditions (including allergies).')
    
    headset = forms.BooleanField(label='Headset requested?',
								 required=False,
								 help_text='Auriez-vous besoin d’un casque d’écoute pour la traduction?<br/>Would you be interested in a simultaneous-translation headset? There will be keynotes in both English and French.')
	
    tshirt = forms.ChoiceField(label='Purchase a National Conference 2013 t-shirt?',
                               choices=TSHIRT_CHOICES,
                               widget=forms.RadioSelect,
                               help_text="""<a href="/site_media/static/images/conference_shirt_2013.png" class="colorbox"><img src='/site_media/static/images/conference_shirt_2013.png' style='width: 250px;' id="confshirt"/></a><br/><em>design subject to small changes</em>""")
    
    handbook = forms.BooleanField(label='Printed conference handbook',
                               required=False,
                               help_text='Would you like a printed copy of the conference handbook?<br/>An electronic copy will also be available, but there is no wi-fi at the conference centre')
    
    cellphone = forms.CharField(label='Your cell phone number',
                                required=False,
                                help_text="(optional) If you wish to receive logistical updates and reminders by text message during the conference")

    emergName = forms.CharField(label='Emergency contact name')
    emergPhone = forms.CharField(label='Emergency contact phone number')

    photo_release = forms.BooleanField(label='Photo release',
                                       required=False,
                                       initial=True,
                                       help_text='I agree to be photographed and/or recorded by Engineers Without Borders Canada as part of my participation in 2013 EWB National Conference, and that they and their successors shall own all rights of every kind in said photography and/or recording.')
    
    #resume = forms.FileField(label='Resume',
    #                         required=False,
    #                         help_text="(optional) Attach a resume if you would like it shared with our sponsors")
    
    #grouping = forms.ChoiceField(label='Which group do you belong to?',
    #                             choices=EXTERNAL_GROUPS,
    #                             required=False)
    #grouping2 = forms.CharField(label='&nbsp;',
    #                            required=False,
    #                            help_text='(if other)')

    class Meta:
        model = ConferenceRegistration
        fields = ['foodPrefs', 'specialNeeds', 'headset', 'tshirt', 'handbook',
                  'cellphone', 'emergName', 'emergPhone', 'photo_release'
                  ]
    
class ConferenceRegistrationForm3(ConferenceRegistrationForm):
    prevConfs = forms.ChoiceField(label='EWB national conferences attended',
								  choices=PASTEVENTS)
    prevRetreats = forms.ChoiceField(label='EWB regional retreats attended',
									 choices=PASTEVENTS)
    new_to_calgary = forms.BooleanField(label='Is this your first time in Calgary?',
                                       required=False)

    homeroom = forms.ChoiceField(label='Conference content',
   							     choices=HOMEROOM_CHOICES,
							     widget=forms.RadioSelect,
                                 help_text="""Which of the above does your involvement with EWB most closely align with?<br/><a href='#' id='confcontentlink'>click here for a description of each option</a>""")

    industry = forms.CharField(label='Industry/field',
                               required=False,
                               help_text='Which industry/field do you work in or study?')


#    survey1 = forms.CharField(label='What are you hoping to learn through conference?',
#                              required=False,
#                              widget=forms.Textarea)
#    survey2 = forms.CharField(label='What are some of the connections you are hoping to make through conference?',
#                              help_text='ie, connections to national office, african programs staff, sponsors, chapter members...',
#                              required=False,
#                              widget=forms.Textarea)
#    survey3 = forms.CharField(label='Reflect on the main opportunities and challenges ahead in your involvement with EWB.  How can your #experience at conference help you capitalize on the opportunities and overcome the challenges?',
#                              required=False,
#                              widget=forms.Textarea)
#    survey4 = forms.CharField(label='How would you define your perfect conference experience?',
#                              required=False,
#                              widget=forms.Textarea)
#    survey5 = forms.CharField(label='In the months leading to conference, how will you stay up to speed with the latest conference news?',
#                              help_text='ie, twitter, myewb, conference website, newsletter...',
#                              required=False,
#                              widget=forms.Textarea)
#    survey6 = forms.CharField(label='On Sunday the 15th, would you be interested in a trip to a) the War Museum, b) skiing? (neither are #included in the cost of conference)',
#                              required=False,
#                              widget=forms.Textarea)
#    survey7 = forms.CharField(label='What type of socials would you be interested in?',
#                              required=False,
#                              widget=forms.Textarea)
#    survey8 = forms.CharField(label='Is there a particular restaurant or style of food that you would be interested in knowing the location #of?',
#                              required=False,
#                              widget=forms.Textarea)

    class Meta:
        model = ConferenceRegistration
#        fields = ['prevConfs', 'prevRetreats', 'new_to_ottawa',
#                  'survey1', 'survey2', 'survey3', 'survey4', 'survey5',
#                  'survey6', 'survey7', 'survey8']
        fields = ['prevConfs', 'prevRetreats', 'new_to_calgary', 'homeroom', 'industry']
    
class ConferenceRegistrationForm4(ConferenceRegistrationForm):
    africaFund = forms.ChoiceField(label='Support an African delegate?',
                                   choices=AFRICA_FUND,
                                   initial='75',
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

class ConferenceRegistrationForm5(ConferenceRegistrationForm):
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
            codename = reg.code.getShortname()
        else:
            codename = "open"
        
        sku = "confreg-2013-" + reg.type + "-" + codename
        
        if not CONF_OPTIONS.get(sku, None):
            errormsg = "The registration code you've entered is not valid for the registration type you selected."
            raise forms.ValidationError("Unable to complete registration (see errors below)")
         
        cost = CONF_OPTIONS[sku]['cost']
        name = CONF_OPTIONS[sku]['name']
        product, created = Product.objects.get_or_create(sku=sku)
        if created:
            product.name = name
            product.amount = cost
            product.save()
            
        cleaned_data['products'].append(product.sku)
        total_cost = total_cost + Decimal(product.amount)

        if needsToRenew(self.user.get_profile(), type=reg.type):
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
            sku = "13-africafund-%d" % cost
            name = "Support an African delegate ($%d)" % cost
            product, created = Product.objects.get_or_create(sku=sku)
            if created:
                product.name = name
                product.amount = cost
                product.save()
            
            cleaned_data['products'].append(product.sku)
            total_cost = total_cost + Decimal(product.amount)

        if reg.tshirt and (reg.tshirt == 's' or reg.tshirt == 'm' or reg.tshirt == 'l' or reg.tshirt == 'x'):
            sku = "13-conf-tshirt"
            name = "Conference t-shirt"
            product, created = Product.objects.get_or_create(sku=sku)
            if created:
                product.name = name
                product.amount = 20
                product.save()
            
            cleaned_data['products'].append(product.sku)
            total_cost = total_cost + Decimal(20)

        if reg.extra_gala:
            sku = "13-conf-galaguest"
            name = "Extra Gala ticket"
            product, created = Product.objects.get_or_create(sku=sku)
            if created:
                product.name = name
                product.amount = 75
                product.save()
            
            cleaned_data['products'].append(product.sku)
            total_cost = total_cost + Decimal(75)

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
            
            if not response[0]:
                response = (False, "Credit card: %s" % response[1])
        
        if response[0] == True:
            if reg.code:
                codename = reg.code.getShortname()
            else:
                codename = "open"
            
            #registration = form.save(commit=False)
            #registration.user = user
            reg.submitted = True
            reg.type = "confreg-2013-" + reg.type + "-" + codename
            reg.amountPaid = CONF_OPTIONS[reg.type]['cost']
            reg.roomSize = reg.type
            reg.receiptNum = response[2]
            reg.txid = response[1]
            
            #if cleaned_data.get('grouping', None):
            #    registration.grouping = cleaned_data['grouping']
            
            reg.save()
            
            # and update their membership if they paid it
            if needsToRenew(request.user.get_profile()):
                request.user.get_profile().pay_membership()
                
            # lastly, add them to the group
            grp, created = Community.objects.get_or_create(slug='conference2013',
                                                           defaults={'invite_only': True,
                                                                     'name': 'National Conference 2013 - EWB delegates',
                                                                     'creator': request.user,
                                                                     'description': 'National Conference 2013 delegates (EWB members)',
                                                                     'mailchimp_name': 'National Conference 2013 members',
                                                                     'mailchimp_category': 'Conference'})

            grp2, created = Community.objects.get_or_create(slug='conference2013-external',
                                                            defaults={'invite_only': True,
                                                                      'name': 'National Conference 2013 - external delegates',
                                                                      'creator': request.user,
                                                                      'description': 'National Conference 2013 delegates (external)',
                                                                      'mailchimp_name': 'National Conference 2013 external',
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
        needsRenewal = needsToRenew(request.user.get_profile())

        print "failing.  going to stage 6.  message is %s" % response[1]

        return render_to_response('conference/registration.html',
                                  {'registration': reg,
                                   'form': form,
                                   'stage': '6',
                                   'last_stage': '5',
                                   'user': request.user,
                                   'needsRenewal': needsRenewal
                                  },
                                  context_instance=RequestContext(request)
                                 )

class CodeGenerationForm(forms.Form):
    type = forms.CharField(max_length=1, label='Type of code')
    start = forms.IntegerField(label='Starting at')
    number = forms.IntegerField(label='How many codes')
    
class ConferenceTShirtForm(forms.Form):
    theuser = None

    _user = None
    def _get_user(self):
        return self._user
    
    def _set_user(self, value):
        self._user = value
        if self.fields.get('address', None):
            self.fields['address'].user = value
            
        #
        #if value.is_bulk:
        #    del(self.fields['prevConfs'])
        #    del(self.fields['prevRetreats'])
        #    #del(self.fields['code'])
        #    self.fields['type'].choices=EXTERNAL_CHOICES
        #else:
        #    del(self.fields['grouping'])
        #    del(self.fields['grouping2'])
            
    user = property(_get_user, _set_user)

    tshirt = forms.ChoiceField(label='Purchase an EWB t-shirt?',
                               choices=TSHIRT_CHOICES)
    
    cc_type = forms.ChoiceField(label='Credit card type',
                                  choices=CC_TYPES)
    cc_number = CreditCardNumberField(label='Credit card number')
    cc_expiry = CreditCardExpiryField(label='Credit card expiry',
                                      help_text='MM/YY')
    billing_name = forms.CharField(label='Name on credit card', max_length=255)
    address = CompactAddressField(label='Billing Address')
    id = forms.IntegerField(widget=forms.HiddenInput, required=False)
    
    trnError = None
    
    def clean_tshirt(self):
        if self.cleaned_data['tshirt']:
            if self.cleaned_data['tshirt'] == 'n':
                raise forms.ValidationError("Please select a t-shirt size")
        return self.cleaned_data['tshirt']
    
        
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
        
        sku = "13-conf-tshirt"
        name = "Conference t-shirt"
        cost = 20
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
    
    
class ConferenceTShirtFormPreview(PaymentFormPreview):
    preview_template = 'conference/tshirtpreview.html'
    form_template = 'conference/purchase.html'
    username = None
    
    def parse_params(self, *args, **kwargs):
        super(ConferenceTShirtFormPreview, self).parse_params(*args, **kwargs)
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
            response = super(ConferenceTShirtFormPreview, self).done(request, cleaned_data)
            
            if not response[0]:
                response = (False, "Credit card: %s" % response[1])
        
        if response[0] == True:
            reg.tshirt = cleaned_data['tshirt']      # somethin like this...
            reg.save()
            
            # don't do the standard render_to_response; instead, do a redirect
            # so that someone can't double-submit by hitting refresh
            request.user.message_set.create(message='T-Shirt order received!')
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

class ConferenceQuestionnaireForm(forms.ModelForm):
    roles = forms.MultipleChoiceField(required=False,
                                      widget=forms.CheckboxSelectMultiple,
                                      choices=ROLES_CHOICES)
    
    class Meta:
            model = ConferenceQuestionnaire
            exclude = ('registration',)

class ConferenceQuestionnaireFormFrench(forms.ModelForm):
    first_conference = forms.BooleanField(label='Est-ce votre premier congrès?',
                                          required=False)
    
    chaptertype = forms.ChoiceField(choices=CHAPTERTYPE_CHOICES_FR,
                                    label='De quel type de section faites-vous partie?')
    
    roles = forms.MultipleChoiceField(required=False,
                                      widget=forms.CheckboxSelectMultiple,
                                      choices=ROLES_CHOICES_FR,
                                      label='Quel est votre rôle actuellement dans ISF :')
    
    leadership_years = forms.ChoiceField(choices=((1, '<= 1'),
                                                  (2, '2 - 3'), 
                                                  (3, '> 3 ')), 
                                         label='Nombre d’années d’expérience dans une position de leadership dans ISF')
    
    leadership_day = forms.BooleanField(label='Êtes-vous inscrit à la Journée du leadership ayant lieu le 11 janvier 2012?',
                                        required=False)
    
    innovation_challenge = forms.BooleanField(label='Êtes-vous inscrit à la "Innovation Challenge"?',
                                              required=False)
    
    prep = forms.ChoiceField(choices=((0, '< 5 heures'),
                                      (5, '> 5 heures')),
                             label='Combien d’heures vous engagez-vous à investir dans votre préparation (lecture/écoute/réflexion) pour le congrès?')

    class Meta:
            model = ConferenceQuestionnaire
            exclude = ('registration',)

