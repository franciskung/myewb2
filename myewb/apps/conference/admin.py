"""myEWB conference admin declarations

This file is part of myEWB
Copyright 2009 Engineers Without Borders (Canada) Organisation and/or volunteer contributors

Created on 2009-10-20
@author Francis Kung
"""

from django.contrib import admin
from conference.models import *

class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('user', 'amountPaid', 'roomSize', 'type',
                    'date', 'headset', 'foodPrefs', 'cancelled', 
                    'specialNeeds', 'emergName', 'emergPhone', 'code',
                    'prevConfs', 'prevRetreats')

admin.site.register(ConferenceRegistration, RegistrationAdmin)

class CodeAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'type', 'number')
    
admin.site.register(ConferenceCode, CodeAdmin)

class TimeslotAdmin(admin.ModelAdmin):
    list_display = ('name', 'day', 'time')
    
admin.site.register(ConferenceTimeslot, TimeslotAdmin)

class SessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'timeslot')
    
admin.site.register(ConferenceSession, SessionAdmin)

class CriteriaAdmin(admin.ModelAdmin):
    list_display = ('session',)
    
admin.site.register(ConferenceSessionCriteria, CriteriaAdmin)

class PrepAdmin(admin.ModelAdmin):
    list_display = ('session', 'name', 'url')
    
admin.site.register(ConferencePrep, PrepAdmin)

