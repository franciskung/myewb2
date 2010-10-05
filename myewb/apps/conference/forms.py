"""myEWB conference registration forms

This file is part of myEWB
Copyright 2009 Engineers Without Borders Canada

Created on 2009-10-18
@author Francis Kung
"""

from datetime import date
from decimal import Decimal
from django import forms
from django.contrib.formtools.preview import FormPreview
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext

from conference.constants import *
from conference.models import ConferenceRegistration, ConferenceCode, InvalidCode
from conference.utils import needsToRenew
from creditcard.models import CC_TYPES, Product
from creditcard.forms import CreditCardNumberField, CreditCardExpiryField, PaymentFormPreview
from siteutils.forms import CompactAddressField
from siteutils.models import Address

class ConferenceRegistrationForm(forms.ModelForm):
    theuser = None

    # bleh.  i don't like putting so much UI text here, instead of in a template!!
    headset = forms.BooleanField(label='Headset requested?',
								 required=False,
								 help_text='Would you use a simultaneous-translation headset for keynote speakers not in your preferred language, if headsets were available?')
	
    foodPrefs = forms.ChoiceField(label='Food preferences',
								  choices=FOOD_CHOICES,
								  widget=forms.RadioSelect,
								  initial='none',
								  help_text='Please use the text area below to provide details or any other requirements, if needed')
    specialNeeds = forms.CharField(label='Special needs',
								   required=False,
								   widget=forms.Textarea,
								   help_text='Please let us know about any special dietary, accessibility or other needs you may have, or any medical conditions (including allergies).')
    
    emergName = forms.CharField(label='Emergency contact name')
    emergPhone = forms.CharField(label='Emergency contact phone number')
    
    prevConfs = forms.ChoiceField(label='EWB national conferences attended',
								  choices=PASTEVENTS)
    prevRetreats = forms.ChoiceField(label='EWB regional retreats attended',
									 choices=PASTEVENTS)
    
    resume = forms.FileField(label='Resume',
                             required=False,
                             help_text="(optional) Attach a resume if you would like to participate in the jobs fair")
    
    cellphone = forms.CharField(label='Cell phone number',
                                required=False,
                                help_text="(optional) If you wish to receive logistical updates and reminders by text message during the conference")
    
    code = forms.CharField(label='Registraton code',
                           help_text='if you have a registration code, enter it here for a discounted rate.')
    type = forms.ChoiceField(label='Registration type',
							 choices=ROOM_CHOICES,
							 widget=forms.RadioSelect,
							 help_text="""<table border='1' class='descform'>
  <tr>
    <th>&nbsp;</th>
    <th>Shared bed</th>
    <th>Single bed</th>
    <th>No room</th>
  </tr>
  <tr>
    <th>University chapters: BC/AB/NF</th>
    <td>$100</td>    
    <td>$220</td>    
    <td>$80</td>    
  </tr>
  <tr>
    <th>University chapters: SK/MB/NB/NS</th>
    <td>$200</td>    
    <td>$320</td>    
    <td>$160</td>    
  </tr>
  <tr>
    <th>University chapters: ON/QB</th>
    <td>$350</td>    
    <td>$470</td>    
    <td>$280</td>    
  </tr>
  <tr>
    <th>Unsubsidized (no registration code)</th>
    <td>$620</td>
    <td>$740</td>    
    <td>$500</td>    
  </tr>
</table>""")
    
    africaFund = forms.BooleanField(label='Support an African delegate?',
								    required=False,
								    help_text='check to contribute an additional $20 (non-refundable) towards a fund to bring young African leaders to the conference as delegates.')

    ccardtype = forms.ChoiceField(label='Credit card type',
								  choices=CC_TYPES)
    cc_number = CreditCardNumberField(label='Credit card number')
    cc_expiry = CreditCardExpiryField(label='Credit card expiry',
                                      help_text='MM/YY')
    billing_name = forms.CharField(label='Name on credit card', max_length=255)
    address = CompactAddressField(label='Billing Address')
        
    # this gets set if the card is declined at the bank
    trnError = None

    class Meta:
        model = ConferenceRegistration
        fields = ['headset', 'foodPrefs', 'specialNeeds', 'emergName', 'emergPhone',
                  'prevConfs', 'prevRetreats', 'resume', 'cellphone', 
                  'code', 'type', 'africaFund']

    def clean_code(self):
        codestring = self.cleaned_data['code'].strip().lower()

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
        # If the card is declined at the bank, trnError will get set...
        if self.trnError:
            raise forms.ValidationError(self.trnError)
        
        if self.errors:
            return None

        # and do some auto-processing as needed
        cleaned_data = self.cleaned_data
        cleaned_data['products'] = []
        total_cost = 0
        
        sku = "confreg-2011-" + cleaned_data['type'] + "-" + cleaned_data['code'].getShortname()
        cost = CONF_OPTIONS[sku]['cost']
        name = CONF_OPTIONS[sku]['name']
        product, created = Product.objects.get_or_create(sku=sku)
        if created:
            product.name = name
            product.amount = cost
            product.save()
            
        cleaned_data['products'].append(product.sku)
        total_cost = total_cost + Decimal(product.amount)

        if needsToRenew(self.user.get_profile()):
            # FIXME: some duplicated code from profiles.forms (where saving membership fees)
            if self.user.get_profile().student():
                type = "studues"
            else:
                type = "produes"

            chapter = self.user.get_profile().get_chapter()
            if chapter:
                type += "-" + chapter.group.slug
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

        if cleaned_data['africaFund'] == True:
            sku = "11-africafund"
            cost = "20"
            name = "Support an African delegate"
            product, created = Product.objects.get_or_create(sku=sku)
            if created:
                product.name = name
                product.amount = cost
                product.save()
            
            cleaned_data['products'].append(product.sku)
            total_cost = total_cost + Decimal(product.amount)

        cleaned_data['total_cost'] = total_cost
        self.cleaned_data = cleaned_data

        return self.cleaned_data
    

    _user = None
    def _get_user(self):
        return self._user
    def _set_user(self, value):
        self._user = value
        if self.fields.get('address', None):
            self.fields['address'].user = value
    user = property(_get_user, _set_user)

class ConferenceRegistrationFormPreview(PaymentFormPreview):
    preview_template = 'conference/preview.html'
    form_template = 'conference/registration.html'
    username = None
    
    def done(self, request, cleaned_data):
        # add profile info, as it's needed for CC processing
        form = self.form(request.POST)
        if not request.user.email or \
            not request.user.get_profile().default_phone():

            # simulate a cred card declined, to trigger form validation failure
            response = (False, "Please fill out your profile information.")

        else:
            cleaned_data['email'] = request.user.email
            cleaned_data['phone'] = request.user.get_profile().default_phone().number
            
            # this call sends it to the bank!!
            response = super(ConferenceRegistrationFormPreview, self).done(request, cleaned_data)
        
        if response[0] == True:
            registration = form.save(commit=False)
            registration.user = request.user
            registration.type = "confreg-2011-" + cleaned_data['type'] + "-" + cleaned_data['code'].getShortname()
            registration.amountPaid = CONF_OPTIONS[registration.type]['cost']
            registration.roomSize = cleaned_data['type']
            registration.code = cleaned_data['code']
            registration.receiptNum = response[2]
            registration.txid = response[1]
            
            registration.save()

            # don't do the standard render_to_response; instead, do a redirect
            # so that someone can't double-submit by hitting refresh
            return HttpResponseRedirect(reverse('confreg'))
        
        else:
            registration = None
            form.trnError = response[1]
            form.clean

        return render_to_response('conference/registration.html',
                                  {'registration': registration,
                                   'form': form
                                   },
                                   context_instance=RequestContext(request)
                                   )

class CodeGenerationForm(forms.Form):
    type = forms.CharField(max_length=1, label='Type of code')
    start = forms.IntegerField(label='Starting at')
    number = forms.IntegerField(label='How many codes')
    