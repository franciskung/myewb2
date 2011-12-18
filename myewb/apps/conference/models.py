import hashlib
from datetime import date, datetime, timedelta
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.translation import ugettext_lazy as _

from communities.models import Community
from conference.constants import *
from networks.models import Network, ChapterInfo
from siteutils.models import Address

class ConferenceRegistration(models.Model):
    """Conference registration data"""
    
    user = models.ForeignKey(User, related_name="conference_registrations")
    chapter = models.ForeignKey(Network, related_name="conference_delegates", null=True)
    
    amountPaid = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    roomSize = models.CharField(max_length=25, null=True, blank=True)
    date = models.DateTimeField(default=datetime.now)
    headset = models.BooleanField(default=False)
    foodPrefs = models.CharField(max_length=10, choices=FOOD_CHOICES, default='none')
    submitted = models.BooleanField(default=False)
    cancelled = models.BooleanField(default=False)
    specialNeeds = models.TextField(null=True, blank=True)
    emergName = models.CharField(max_length=255, null=True, blank=True)
    emergPhone = models.CharField(max_length=50, null=True, blank=True)
    prevConfs = models.SmallIntegerField(default=0)
    prevRetreats = models.SmallIntegerField(default=0)
    cellphone = models.CharField(max_length=50, blank=True, null=True)
    cellphone_optout = models.DateTimeField(blank=True, null=True)
    cellphone_from = models.ForeignKey('ConferencePhoneFrom', null=True, blank=True)
    #grouping = models.CharField(max_length=50, blank=True, null=True)
    roommate = models.CharField(max_length=255, blank=True, null=True)
    new_to_ottawa = models.BooleanField(default=False, blank=True)
    
    txid = models.CharField(max_length=255, null=True, blank=True)
    receiptNum = models.CharField(max_length=255, null=True, blank=True)
    code = models.ForeignKey('ConferenceCode', related_name="registration", blank=True, null=True)
    type = models.CharField(max_length=50, null=True, blank=True)
    africaFund = models.SmallIntegerField(blank=True, null=True)
    tshirt = models.CharField(max_length=1, blank=True, null=True)
    
    survey1 = models.TextField(null=True, blank=True)
    survey2 = models.TextField(null=True, blank=True)
    survey3 = models.TextField(null=True, blank=True)
    survey4 = models.TextField(null=True, blank=True)
    survey5 = models.TextField(null=True, blank=True)
    survey6 = models.TextField(null=True, blank=True)
    survey7 = models.TextField(null=True, blank=True)
    survey8 = models.TextField(null=True, blank=True)

    def cancel(self):
        self.cancelled = True
        self.chapter = None
        self.save()

        # remove from delegates group
        grp, created = Community.objects.get_or_create(slug='conference2012',
                                                       defaults={'invite_only': True,
                                                                 'name': 'National Conference 2012 - EWB delegates',
                                                                 'creator': self.user,
                                                                 'description': 'National Conference 2012 delegates (EWB members)',
                                                                 'mailchimp_name': 'National Conference 2012 members',
                                                                 'mailchimp_category': 'Conference'})

        grp2, created = Community.objects.get_or_create(slug='conference2011-external',
                                                        defaults={'invite_only': True,
                                                                  'name': 'National Conference 2012 - external delegates',
                                                                  'creator': self.user,
                                                                  'description': 'National Conference 2012 delegates (external)',
                                                                  'mailchimp_name': 'National Conference 2012 external',
                                                                  'mailchimp_category': 'Conference'})

        grp.remove_member(self.user)
        grp2.remove_member(self.user)
        
        # re-enable code
        if self.code and self.code.expired:
            self.code.expired = False
            self.code.save()
        
    def getRefundAmount(self):
        return self.amountPaid - 20

class InvalidCode(Exception):
    def __init__(self, value):
        self.value = value
    
    def __str__(self):
        return repr(self.value)
    
class ConferenceCode(models.Model):
    """Registration code"""

    code = models.CharField(max_length=9)
    type = models.CharField(max_length=1, choices=CONF_CODES)
    number = models.IntegerField()
    
    generated = models.DateTimeField(default=datetime.now)
    
    # currently needs to be done manually, but fairly easy to write a UI for this
    expired = models.BooleanField(default=False)
    
    # not currently used, but may let us enforce code/chapter pairings
    chapter = models.ForeignKey(Network, related_name="conference_codes", verbose_name=_('chapter'), null=True)
    
    def __init__(self, *args, **kwargs):
        super(ConferenceCode, self).__init__(*args, **kwargs)
    
        # try/except to keep the admin page working
        try:
            self.type = kwargs['type']
            self.number = kwargs['number']
        
            self.expired = False

            m = hashlib.md5()
            m.update("%s%03d%s" % (self.type, self.number, CONF_HASH))
            self.code = "%s%03d%s" % (self.type, self.number, m.hexdigest()[:4])
        except:
            pass

    def getShortname(self):
        # CONF_CODES is a tuple so that it can be used as a choices= for 
        # the type field above... so we hack it here to make it act like a
        # dictionary
        for code in CONF_CODES:
            if code[0] == self.type.lower():
                return code[1]
        
        # should never get here, since the type field is restricted to CONF_CODES
        return "unknown"
    
    def getLongname(self):
        for code in CONF_CODES_LONG:
            if code[0] == self.type.lower():
                return code[1]
        return "unknown"
    
    def isAvailable(self):
        if self.expired == True:
            return False
        
        try:
            ConferenceCode.objects.get(code=self.code, registration__submitted=True, registration__cancelled=False)
        except ObjectDoesNotExist:
            return True
        except:
            pass

        return False

    @staticmethod
    def isValid(code):
        type = code[0]
        number = code[1:3]
        codehash = code[4:]
        
        m = hashlib.md5()
        m.update("%s%s%s" % (type, number, CONF_HASH))
        return codehash == m.hexdigest()[:4]

class AlumniConferenceCode(ConferenceCode):
    def getShortname(self):
        return 'alumni'
    
    def isAvailable(self):
        return True
    
class QuasiVIPCode(ConferenceCode):
    def getShortname(self):
        return 'discounted'
    
    def isAvailable(self):
        return True
        
class FriendsConferenceCode(ConferenceCode):
    def getShortname(self):
        return 'friends'
        
    def isAvailable(self):
        return True

SESSION_TYPES = (('keynote', "Keynote"),
                 ('speaker', "Speaker"),
                 ('panel', "Panel discussion"),
                 ('workshop', "Workshop"),
                 ('social', "Social time"),
                 ('networking', "Networking"),
                 ('other', "Other"))
                 
STREAMS = (('common', 'Common sessions'),
           ('coalitions', 'Coalitions for Change'),
           ('aprosperity', 'Unlocking African Prosperity'),
           ('rethinking', 'Rethinking Development'),
           ('internal', 'Internal Meetings'))
STREAMS_SHORT = (('aprosperity', 'African Prosperity'),
                 ('coalitions', 'Coalitions'),
                 ('rethinking', 'Rethinking Devt'))

class ConferenceTimeslot(models.Model):
    name = models.CharField(max_length=255)
    day = models.DateField(help_text='yyyy-mm-dd')
    time = models.TimeField(help_text='hh:mm in 24-hour time. must be either :00 or :30 to show up on schedules')
    length = models.IntegerField(help_text="in minutes")
    common = models.BooleanField(default=False)

    class Meta:
        ordering = ('day', 'time', 'length')
        
    def __unicode__(self):
        return "" + str(self.day) + " " + str(self.time) + " - " + str(self.name)
        #return self.name

    def endtime(self):
        return datetime.combine(date.today(), self.time) + timedelta(minutes=self.length)
                 
class ConferenceSession(models.Model):
    name = models.CharField(max_length=255)
    room = models.CharField(max_length=255, blank=True)
    #sessiontype = models.CharField(max_length=50, choices=SESSION_TYPES, blank=True, null=True)
    #short_description = models.TextField(blank=True)
    #long_description = models.TextField(blank=True)
    description = models.TextField(blank=True)
    timeslot = models.ForeignKey(ConferenceTimeslot)
    common = models.BooleanField(default=False)
    
    #stream = models.CharField(max_length=50, choices=STREAMS)
    capacity = models.IntegerField(blank=True, null=True)
    
    attendees = models.ManyToManyField(User, related_name="conference_sessions", blank=True)
    #maybes = models.ManyToManyField(User, related_name="conference_maybe")
    
#    class Meta:
#        ordering = ('day', 'time', 'stream', 'length')
#        ordering = ('day', 'time', 'length')
        
    def __unicode__(self):
        return str(self.id) + " - " + str(self.name) + " (" + str(self.timeslot) + ")"

    def url(self):
        return reverse('conference_session', kwargs={'session': self.id});
        
    def dayverbose(self):
        if self.timeslot.day == date(year=2012, month=1, day=12):
            return 'thurs'
        elif self.timeslot.day == date(year=2012, month=1, day=13):
            return 'fri'
        elif self.timeslot.day == date(year=2012, month=1, day=14):
            return 'sat'
        
        return ''
        
    def timeverbose(self):
        return "%02d%02d" % (self.timeslot.time.hour, self.timeslot.time.minute)
        
    #def streamverbose(self):
    #    for sid, sname in STREAMS:
    #        if self.stream == sid:
    #            return sname
              
    def user_is_attending(self, user):
        if user.is_authenticated():
            if user in self.attendees.all():
                return True
        return False
        
    #def user_is_tentative(self, user):
    #    if user.is_authenticated():
    #        if user in self.maybes.all():
    #            return True
    #    return False
        
    def popular(self):
        # TODO: I could probably come up with a better algorithm, which takes
        # into account how many people have set up schedules...
        if self.capacity and self.attendees.count() + (self.maybes.count() / 2) > self.capacity * 0.5:
            return True
        
        return False
        
    #def fixed(self):
    #    if self.stream == 'common':
    #        return True
    #    else:
    #        return False
    
class ConferenceQuestionnaire(models.Model):
    registration = models.OneToOneField(ConferenceRegistration)
    
    first_conference = models.BooleanField(default=True,
                                           verbose_name='Is this your first EWB National Conference?')
    
    chaptertype = models.CharField(max_length=10, choices=CHAPTERTYPE_CHOICES,
                                   verbose_name='What type of chapter are you from?')
    
    roles = models.CharField(max_length=255, choices=ROLES_CHOICES, blank=True,
                             verbose_name='What role(s) do you currently hold in EWB, if any?')
    
    leadership_years = models.IntegerField(blank=True, choices=(('1', '1 or less'),
                                                                ('2', '2 - 3'), 
                                                                ('3', '3 or more')), 
                                           verbose_name='How many years have you held a leadership position in EWB?',
                                           default=1)
    
    leadership_day = models.BooleanField(default=False,
                                         verbose_name='Are you attending leadership day?')
    
    innovation_challenge = models.BooleanField(default=False,
                                               verbose_name='Are you participating in the Innovation Challenge?')
    
    prep = models.IntegerField(choices=(('0', 'Under 5 hours'),
                                        ('5', 'Over 5 hours')),
                                        verbose_name='How many hours of prep are you able to commit to before conference?')
                                        
class ConferenceSessionCriteria(models.Model):
    first_conference = models.CharField(max_length=3, choices=(('yes', 'yes'), ('no', 'no')), blank=True)
    chaptertype = models.CharField(max_length=10, choices=CHAPTERTYPE_CHOICES, blank=True, null=True)
    roles = models.CharField(max_length=50, choices=ROLES_CHOICES, blank=True, null=True)
    leadership_years = models.IntegerField(blank=True, choices=(('1', '1 or less'),
                                                                ('2', '2 - 3'), 
                                                                ('3', '3 or more')), 
                                           null=True)
    leadership_day = models.CharField(max_length=3, choices=(('yes', 'yes'), ('no', 'no')), blank=True)
    innovation_challenge = models.CharField(max_length=3, choices=(('yes', 'yes'), ('no', 'no')), blank=True)
    prep = models.IntegerField(choices=(('0', 'Under 5 hours'),
                                        ('5', 'Over 5 hours')),
                                       blank=True, null=True)
    past_session = models.ForeignKey(ConferenceSession, related_name='past_session',
                                     blank=True, null=True)
    
    other = models.BooleanField(default=False, blank=True)
                                        
    session = models.ForeignKey(ConferenceSession)
    
    def __unicode__(self):
        return str(self.session) + " criteria"
        
class ConferencePrep(models.Model):
    session = models.ForeignKey(ConferenceSession)
    url = models.CharField(max_length=255)
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.session + " prep: " + self.name
        
class ConferencePhoneFrom(models.Model):
    number = models.CharField(max_length=10)
    accounts = models.IntegerField(default=0)

class ConferenceCellNumber(models.Model):
    cellphone = models.CharField(max_length=10)
    opt_in = models.DateTimeField(auto_now_add=True)
    cellphone_optout = models.DateTimeField(blank=True, null=True)
    cellphone_from = models.ForeignKey(ConferencePhoneFrom, null=True, blank=True)
