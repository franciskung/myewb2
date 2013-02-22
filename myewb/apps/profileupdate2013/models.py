from django import forms
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType

from profiles.models import MemberProfile
from datetime import date, datetime

class ProfileUpdate(models.Model):
    user = models.ForeignKey(User)
    profile = models.ForeignKey(MemberProfile)
    
    started = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)
    
    contact = models.DateTimeField(blank=True, null=True, editable=False)
    workplace = models.DateTimeField(blank=True, null=True, editable=False)
    interests = models.DateTimeField(blank=True, null=True, editable=False)
    demographics = models.DateTimeField(blank=True, null=True, editable=False)
    
    INVOLVEMENT = (('own', 'I am helping shape the direction of EWB'),
                   ('active', 'I am actively involved in EWB'),
                   ('contributing', 'I am occassionally involved in EWB'),
                   ('passive', 'I follow news and updates from EWB'),
                   ('inactive', 'I do not feel connected to EWB'))
    current_involvement = models.TextField(choices=INVOLVEMENT,
                                           max_length=50,
                                           verbose_name='Which statement best describes your relationship to EWB?')
                                           
    ROLES = (('exec', 'I help lead an EWB chapter'),
             ('chapter', 'I participate in an EWB chapter'),
             ('distrib', 'I am involved in a Distributed Team'),
             ('newsletter', "I actively follow EWB newsletters and updates"),
             ('donor', 'I am a donor to EWB'),
             ('aps', 'I work for EWB full-time (APS or staff member)'),
             ('alumni', 'I was previously involved but am no longer involved ("alumni")'))
    roles = models.TextField(max_length=50,
                             verbose_name='Which roles do you play in EWB? (check all that apply)')

    GOALS = (('changemaking', 'Actively contributing to social change'),
             ('leadership', 'Leadership and personal development opportunities'),
             ('community', 'A community of socially-conscious peers and friends'),
             ('discussion', 'Discussions on interesting and relevant topics'),
             ('venture', 'An audience for a project or venture that I want to promote'),
             ('engineering', 'Applying my technical engineering skills'),
             ('other', 'Other'))
    goals = models.TextField(max_length=50,
                             verbose_name='Why are you apart of EWB? (check all that apply)')

class ProfileUpdateForm(forms.ModelForm):
    current_involvement = forms.ChoiceField(required=False,
                                            choices=ProfileUpdate.INVOLVEMENT,
                                            widget=forms.RadioSelect(),
                                            label='Which statement best describes your relationship to EWB?')

    roles = forms.CharField(required=False,
                            widget=forms.CheckboxSelectMultiple(choices=ProfileUpdate.ROLES),
                            label='Which roles do you play in EWB? (check all that apply)')

    goals = forms.CharField(required=False,
                            widget=forms.CheckboxSelectMultiple(choices=ProfileUpdate.GOALS),
                            label='Why are you apart of EWB? (check all that apply)')
    
    class Meta:
        model = ProfileUpdate
        fields = ('current_involvement', 'roles', 'goals')

    def validate_roles(data):
        return 
