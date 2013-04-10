# -*- coding: utf-8 -*- 

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
    INVOLVEMENT_FR = (('own', "J'aide à définir la direction d'ISF."),
                   ('active', "Je m'implique activement dans ISF."),
                   ('contributing', "Je m'implique occasionnellement dans ISF."),
                   ('passive', "Je suis les nouvelles et les mises à jour d'ISF."),
                   ('inactive', "Je ne suis pas connecté(e) à ISF."))
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
    ROLES_FR = (('exec', "J'aide à diriger une section d'ISF."),
             ('chapter', "Je participe à une section d'ISF."),
             ('distrib', "Je suis impliqué(e) dans une équipe décentralisée."),
             ('newsletter', "Je suis activement les infolettres et mises à jour d’ISF."),
             ('donor', "Je suis un donateur d'ISF."),
             ('aps', "Je travaille à temps plein pour ISF (PPA ou membre du personnel)."),
             ('alumni', "J'étais impliqué(e) auparavant, je ne suis plus impliqué(e) (\"anciens\")."))
    roles = models.TextField(max_length=50,
                             verbose_name='Which roles do you play in EWB? (check all that apply)')

    GOALS = (('changemaking', 'Actively contributing to social change'),
             ('leadership', 'Leadership and personal development opportunities'),
             ('community', 'A community of socially-conscious peers and friends'),
             ('discussion', 'Discussions on interesting and relevant topics'),
             ('venture', 'An audience for a project or venture that I want to promote'),
             ('engineering', 'Applying my technical engineering skills'),
             ('other', 'Other'))
    GOALS_FR = (('changemaking', 'Contribuer activement au changement social'),
             ('leadership', 'Des possibilités de leadership et de développement personnel'),
             ('community', "Une communauté d'ami(e)s et de pairs socialement responsables"),
             ('discussion', 'Les discussions sur les sujets intéressants et pertinents'),
             ('venture', 'Un public pour un projet ou une initiative que je veux promouvoir'),
             ('engineering', "Appliquer mes compétences techniques d'ingénierie"),
             ('other', 'Autre'))
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

class ProfileUpdateFormFR(ProfileUpdateForm):
    current_involvement = forms.ChoiceField(required=False,
                                            choices=ProfileUpdate.INVOLVEMENT_FR,
                                            widget=forms.RadioSelect(),
                                            label='Lequel des énoncés suivants décrit le mieux votre lien avec ISF?')

    roles = forms.CharField(required=False,
                            widget=forms.CheckboxSelectMultiple(choices=ProfileUpdate.ROLES_FR),
                            label='Quel(s) rôle(s) jouez-vous dans ISF? (cochez toutes les cases qui s’appliquent)')

    goals = forms.CharField(required=False,
                            widget=forms.CheckboxSelectMultiple(choices=ProfileUpdate.GOALS_FR),
                            label="Pourquoi faites-vous partie d'ISF? (cochez toutes les cases qui s'appliquent)")
    

