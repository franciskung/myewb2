"""myEWB conference admin declarations

This file is part of myEWB
Copyright 2009 Engineers Without Borders (Canada) Organisation and/or volunteer contributors

Created on 2009-10-20
@author Francis Kung
"""

from django.contrib import admin
from conference.models import *

class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('user', 'amountPaid', 'type', 'hotel',
                    'date', 'headset', 'foodPrefs', 'cancelled', 
                    'specialNeeds', 'emergName', 'emergPhone', 'code',
                    'prevConfs', 'prevRetreats')

admin.site.register(ConferenceRegistration, RegistrationAdmin)

class CodeAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'type', 'number')
    
admin.site.register(ConferenceCode, CodeAdmin)

class TimeslotAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'day', 'time')
    
admin.site.register(ConferenceTimeslot, TimeslotAdmin)

class SessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'timeslot')
    exclude = ('attendees',)
    
admin.site.register(ConferenceSession, SessionAdmin)

class CriteriaAdmin(admin.ModelAdmin):
    list_display = ('session',)
    
admin.site.register(ConferenceSessionCriteria, CriteriaAdmin)

class PrepAdmin(admin.ModelAdmin):
    list_display = ('session', 'name', 'url')
    
admin.site.register(ConferencePrep, PrepAdmin)

