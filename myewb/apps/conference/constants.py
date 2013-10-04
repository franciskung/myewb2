# coding=utf-8

from django.utils.translation import ugettext_lazy as _
import settings

from networks.models import Network

CONF_HASH = settings.CONF_HASH

WHOAREYOU_CHOICES = (('member', 'I am an EWB member'),
                     ('alumni', 'I am an EWB alumnus'),
                     ('sponsor', 'I am a Conference Sponsor Representative'),
                     ('speaker', 'I am a Conference Speaker/Facilitator'),
                     ('partnerngo', 'I am a NGO partner organization representative'),
                     ('partnerorg', 'I am a partner organization representative'),
                     ('public', 'I am a member of the public'))

chapters = Network.objects.filter(chapter_info__isnull=False, is_active=True).order_by('name')
CHAPTER_CHOICES = [('none','None')]
for c in chapters:
    CHAPTER_CHOICES.append((c.slug, c.name))

ROLES_CHOICES = (('staff', 'Staff'),
                 ('distrib', 'Distributed team member'),
                 ('president', 'Chapter president'),
                 ('exec', 'Chapter executive'),
                 ('jf2014', 'Junior Fellow 2014'),
                 ('jf2013', 'Junior Fellow 2013'),
                 ('pro2013', 'Professional Fellow 2013'),
                 ('confteam', 'Conference team'))
                 
PASTEVENTS = (('0', '0'),
              ('1', '1'),
              ('2', '2'),
              ('3', '3'),
              ('4', '4'),
              ('5', '5'),
              ('6', '6'),
              ('7', '7'),
              ('8', '8'),
              ('9', '9'),
              ('10', '10'),
              ('11', '11'),
              ('12', '12'),
              )

CONF_OPTIONS = {'public': {'name': 'Public registration',
                           'cost': 500},
                'partner': {'name': 'Partner organization',
                           'cost': 475},
                'ngo': {'name': 'Partner organization- NGO',
                           'cost': 400},
                'govt': {'name': 'Government',
                           'cost': 450},
                'alumni': {'name': 'EWB Alumni',
                           'cost': 425},
                'ewb': {'name': 'EWB member (with registration code)',
                           'cost': 589}}

REGISTRATION_CHOICES = []
for c1, c2 in CONF_OPTIONS.iteritems():
    REGISTRATION_CHOICES.append((c1, c2['name']),)
REGISTRATION_CHOICES.reverse()

# this should be a dictionary, but needs to be a tuple to be used as an ENUM
CONF_CODES = (('a', "test"),
              ('b', "student6"),
              ('c', "student5"),
              ('d', "student4"),
              ('e', "student3"),
              ('f', "student2"),
              ('g', "student1"),
              ('h', "city6"),
              ('i', "city5"),
              ('j', "city3"),
              ('k', "city2"),
              ('l', "city1"),
              ('m', "staff"),
              ('n', "facilitator"),
              ('o', "contributor"),
              ('p', "extguest"),
             )
              
CONF_CODE_COSTS = {'test': {'name': "Test code",
                            'cost': 0},
                   'student6': {'name': "Student - zone 6",
                            'cost': 50},
                   'student5': {'name': "Student - zone 5",
                            'cost': 100},
                   'student4': {'name': "Student - zone 4",
                            'cost': 150},
                   'student3': {'name': "Student - zone 3",
                            'cost': 200},
                   'student2': {'name': "Student - zone 2",
                            'cost': 300},
                   'student1': {'name': "Student - zone 1",
                            'cost': 350},
                   'city6': {'name': "City network - zone 6",
                            'cost': 100},
                   'city5': {'name': "City network - zone 5",
                            'cost': 150},
                   'city3': {'name': "City network - zone 3",
                            'cost': 250},
                   'city2': {'name': "City network - zone 2",
                            'cost': 350},
                   'city1': {'name': "City network - zone 1",
                            'cost': 400},
                   'staff': {'name': "EWB staff and guests",
                            'cost': 0},
                   'facilitator': {'name': "Facilitators",
                            'cost': 185},
                   'contributor': {'name': "Contributors",
                            'cost': 300},
                   'extguest': {'name': "External guests",
                            'cost': 300},
                    }

for c1, c2 in CONF_CODE_COSTS.iteritems():
    CONF_OPTIONS[c1] = c2

CONF_CODES_LONG = []
for c1, c2 in CONF_CODES:
    CONF_CODES_LONG.append((c1, CONF_CODE_COSTS[c2]['name']))
CONF_CODES_LONG.reverse()
                   
HOTEL_OPTIONS = {'hotelquad': {'name': 'Hotel room - quad occupancy',
                           'cost': 115},
                 'hoteldouble': {'name': 'Hotel room - double occupancy',
                           'cost': 230},
                 'hotelsingle': {'name': 'Hotel room - single occupancy',
                           'cost': 460},
                 'transportation': {'name': 'Daily transportation from Union Station (no hotel)',
                           'cost': 37},
                 'none': {'name': 'No hotel - no transportation',
                           'cost': 0}}

HOTEL_CHOICES = []
for c1, c2 in HOTEL_OPTIONS.iteritems():
    HOTEL_CHOICES.append((c1, c2['name']),)
HOTEL_CHOICES.reverse()

HOTELGENDER_CHOICES = (('male', 'Delegates identifying as male'),
                        ('female', 'Delegates identifying as female'),
                        ('nopref', 'No preference'),
                        ('other', 'Other (please explain below)'))

HOTELSLEEP_CHOICES = (('nopref', 'No preference'),
                        ('early', 'People who sleep early (before 11pm)'),
                        ('later', 'People who sleep later (11pm - 1am)'),
                        ('vlate', 'People who sleep very late (after 1am)'))
                
HOTELREQUESTS_CHOICES = (('nodrinking', "People who won't drink alcohol during conference (note: implies you will not drink either)"),
                        ('nosmoking', "People who won't smoke during conference (note: implies you will not smoke either. All hotel and conference rooms are non-smoking."))
                        
FOOD_CHOICES = (('none', _("no special preferences")),
                ('vegetarian', _("vegetarian")),
                ('vegan', _("vegan"))
    )
    
DIETARY_CHOICES = (('kosker', 'Kosher'),
                    ('halal', 'Halal'),
                    ('nopeanuts', 'Peanut allergy'),
                    ('celiac', 'Celiac'),
                    ('glutenfree', 'Gluten Free (you are sensitive to gluten but your food can be prepared in close proximity to wheat)'),
                    ('noredmeat', 'No red meat'),
                    ('nopork', 'No pork'),
                    ('nobeef', 'No beef'),
                    ('nonuts', 'Tree nut allergy'),
                    ('noshellfish', 'Shellfish allergy'),
                    ('lactose', 'Lactose intolerent'))


AFRICA_FUND = (('75', 'Yes - $75'),
               ('45', 'Yes - $45'),
               ('20', 'Yes - $20'),
               ('other', 'Yes - other'),
               ('', 'No thank you'))




ROLES_CHOICES_FR = (('president', 'Président(e) de section étudiante ou professionnelle'),
                 ('finance', "Membre de l'équipe des finances"),
                 ('advocacy', "Membre de l'équipe de plaidoyer"),
                 ('youth', "Membre de l'équipe d’engagement des jeunes"),
                 ('members', "Membre de l'équipe d’éducation des membres"),
                 ('communications', "Membre de l'équipe des communications"),
                 ('webmaster', "Webmestre / Administrateur de site / Gestionnaire Web"),
                 ('fundraising', "Membre de l'équipe de collecte de fonds"),
                 ('engineering', "Membre de l'équipe de génie global"),
                 ('fairtrade', "Membre de l'équipe de commerce équitable"),
                 ('otherexec', "Autre rôle exécutif"),
                 ('pastjf', "Ancien JF"),
                 ('currentjf', "JF 2012"),
                 ('alumni', "Ancien membre"),
                 ('distributed', "Membre d'une équipe décentralisée (passé ou présent)"),
                 ('aps', "PPA (passé ou présent)PPA (passé ou présent)"),
                 ('office', "Employé du bureau national ou stagiaire en changement social (passé ou présent)"))
                 
CHAPTERTYPE_CHOICES_FR = (('none', 'Non affilié(e) à une section'),
                       ('city', 'Section professionelle'),
                       ('enguni', 'Section universitaire anglophone'),
                       ('fruni', 'Section universitaire francophone'))

