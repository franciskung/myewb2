# coding=utf-8

from django.utils.translation import ugettext_lazy as _
import settings

FOOD_CHOICES = (('none', _("no special preferences")),
                ('vegetarian', _("vegetarian")),
                ('vegan', _("vegan"))
    )

HOMEROOM_CHOICES = (('yv', 'Youth venture'),
                    ('ge', 'Global Engineering'),
                    ('adv', 'Advocacy'),
                    ('ml', 'Member Learning'),
                    ('net', 'Network / people'),
                    ('ip', 'Invested Partnerships'),
                    ('comms', 'Communications'),
                    ('ft', 'Fair Trade'),
                    ('aps', 'African ventures engagement'),
    )


# this should be a dictionary, but needs to be a tuple to be used as an ENUM
CONF_CODES = (('a', "test"),
              ('b', "uni-east"),
              ('c', "uni-onqb"),
              ('d', "uni-west"),
              ('e', "uni-alberta"),
              ('f', "staff"),
              ('g', "city-onqb"),
              ('h', "city-west"),
              ('i', "city-alberta"),
#              ('j', "alumni"),
             )
              
CONF_CODES_LONG = (('a', "Test code"),
                   ('b', "University chapter (NB/NS/NL)"),
                   ('c', "University chapter (ON/QB)"),
                   ('d', "University chapter (BC/SK/MB)"),
                   ('e', "University chapter (AB)"),
                   ('f', "EWB Staff"),
                   ('g', "City network (ON/QB)"),
                   ('h', "City network (BC/SK/MB)"),
                   ('i', "City network (AB)"),
#                   ('j', "EWB Alumni"),
                  )
              
CONF_HASH = settings.CONF_HASH
    
CONF_OPTIONS = {'confreg-2013-quad-test': {'cost': 175,
                                            'name': "Test - quad occupancy"},
                'confreg-2013-double-test': {'cost': 305,
                                            'name': "Test - double occupancy"},
                'confreg-2013-single-test': {'cost': 600,
                                            'name': "Test - single occupancy"},
                'confreg-2013-nohotel-test': {'cost': 140,
                                            'name': "Test - no room"},

                #'confreg-2013-quad-open': {'cost': 620,
                #                               'name': "Open registration (unsubsidized) - quad occupancy"},
                #'confreg-2013-double-open': {'cost': 740,
                #                               'name': "Open registration (unsubsidized) - double occupancy"},
                #'confreg-2013-single-open': {'cost': 990,
                #                               'name': "Open registration (unsubsidized) - single occupancy"},
                'confreg-2013-nohotel-open': {'cost': 425,
                                               'name': "Open registration (unsubsidized) - no room"},

#                'confreg-2013-friday-open': {'cost': 120,
#                                               'name': "Friday attendance"},
#                'confreg-2013-saturday-open': {'cost': 120,
#                                               'name': "Saturday attendance"},
#                'confreg-2013-twoday-open': {'cost': 220,
#                                               'name': "Friday/Saturday attendance"},
#                'confreg-2013-fridaystudent-open': {'cost': 60,
#                                               'name': "Friday attendance (student)"},
#                'confreg-2013-saturdaystudent-open': {'cost': 60,
#                                               'name': "Saturday attendance (student)"},
#                'confreg-2013-twodaystudent-open': {'cost': 110,
#                                               'name': "Friday/Saturday attendance (student)"},
#
#                'confreg-2013-friday-discounted': {'cost': 100,
#                                               'name': "Friday attendance (discounted)"},
#                'confreg-2013-saturday-discounted': {'cost': 100,
#                                               'name': "Saturday attendance (discounted)"},
#                'confreg-2013-twoday-discounted': {'cost': 180,
#                                               'name': "Friday/Saturday attendance (discounted)"},
#                'confreg-2013-fridaystudent-discounted': {'cost': 60,
#                                               'name': "Friday attendance (student)"},
#                'confreg-2013-saturdaystudent-discounted': {'cost': 60,
#                                               'name': "Saturday attendance (student)"},
#                'confreg-2013-twodaystudent-discounted': {'cost': 110,
#                                               'name': "Friday/Saturday attendance (student)"},
#
#                'confreg-2013-friday-friends': {'cost': 80,
#                                                'name': "Friday/Saturday attendance (friends)"},
#                'confreg-2013-saturday-friends': {'cost': 80,
#                                                'name': "Friday/Saturday attendance (friends)"},
#                'confreg-2013-twoday-friends': {'cost': 160,
#                                                'name': "Friday/Saturday attendance (friends)"},
#                'confreg-2013-fridaystudent-friends': {'cost': 60,
#                                               'name': "Friday attendance (student)"},
#                'confreg-2013-saturdaystudent-friends': {'cost': 60,
#                                               'name': "Saturday attendance (student)"},
#                'confreg-2013-twodaystudent-friends': {'cost': 110,
#                                               'name': "Friday/Saturday attendance (student)"},
#
#                'confreg-2013-friday-staff': {'cost': 0,
#                                                'name': "Friday/Saturday attendance (complimentary)"},
#                'confreg-2013-saturday-staff': {'cost': 0,
#                                                'name': "Friday/Saturday attendance (complimentary)"},
#                'confreg-2013-twoday-staff': {'cost': 0,
#                                                'name': "Friday/Saturday attendance (complimentary)"},
#                'confreg-2013-fridaystudent-staff': {'cost': 0,
#                                               'name': "Friday attendance (complimentary)"},
#                'confreg-2013-saturdaystudent-staff': {'cost': 0,
#                                               'name': "Saturday attendance (complimentary)"},
#                'confreg-2013-twodaystudent-staff': {'cost': 0,
#                                               'name': "Friday/Saturday attendance (complimentary)"},
                
                'confreg-2013-quad-uni-east': {'cost': 200,
                                               'name': "University chapter (NB/NS/NL) - quad occupancy"},
                'confreg-2013-double-uni-east': {'cost': 400,
                                               'name': "University chapter (NB/NS/NL) - double occupancy"},
                'confreg-2013-single-uni-east': {'cost': 700,
                                               'name': "University chapter (NB/NS/NL) - single occupancy"},
                'confreg-2013-nohotel-uni-east': {'cost': 50,
                                               'name': "University chapter (NB/NS/NL) - no room"},

                'confreg-2013-quad-uni-onqb': {'cost': 300,
                                               'name': "University chapter (ON/QB) - quad occupancy"},
                'confreg-2013-double-uni-onqb': {'cost': 500,
                                               'name': "University chapter (ON/QB) - double occupancy"},
                'confreg-2013-single-uni-onqb': {'cost': 800,
                                               'name': "University chapter (ON/QB) - single occupancy"},
                'confreg-2013-nohotel-uni-onqb': {'cost': 150,
                                               'name': "University chapter (ON/QB) - no room"},

                'confreg-2013-quad-uni-west': {'cost': 375,
                                               'name': "University chapter (BC/SK/MB) - quad occupancy"},
                'confreg-2013-double-uni-west': {'cost': 575,
                                               'name': "University chapter (BC/SK/MB) - double occupancy"},
                'confreg-2013-single-uni-west': {'cost': 875,
                                               'name': "University chapter (BC/SK/MB) - single occupancy"},
                'confreg-2013-nohotel-uni-west': {'cost': 225,
                                               'name': "University chapter (BC/SK/MB) - no room"},

                'confreg-2013-quad-uni-alberta': {'cost': 450,
                                               'name': "University chapter (AB) - quad occupancy"},
                'confreg-2013-double-uni-alberta': {'cost': 650,
                                               'name': "University chapter (AB) - double occupancy"},
                'confreg-2013-single-uni-alberta': {'cost': 950,
                                               'name': "University chapter (AB) - single occupancy"},
                'confreg-2013-nohotel-uni-alberta': {'cost': 300,
                                               'name': "University chapter (AB) - no room"},

                'confreg-2013-quad-city-onqb': {'cost': 400,
                                               'name': "City network (ON/QB) - quad occupancy"},
                'confreg-2013-double-city-onqb': {'cost': 600,
                                               'name': "City network (ON/QB) - double occupancy"},
                'confreg-2013-single-city-onqb': {'cost': 900,
                                               'name': "City network (ON/QB) - single occupancy"},
                'confreg-2013-nohotel-city-onqb': {'cost': 250,
                                               'name': "City network (ON/QB) - no room"},

                'confreg-2013-quad-city-west': {'cost': 475,
                                               'name': "City network (BC/SK/MB) - quad occupancy"},
                'confreg-2013-double-city-west': {'cost': 675,
                                               'name': "City network (BC/SK/MB) - double occupancy"},
                'confreg-2013-single-city-west': {'cost': 975,
                                               'name': "City network (BC/SK/MB) - single occupancy"},
                'confreg-2013-nohotel-city-west': {'cost': 325,
                                               'name': "City network (BC/SK/MB) - no room"},

                'confreg-2013-quad-city-alberta': {'cost': 550,
                                               'name': "City network (AB) - quad occupancy"},
                'confreg-2013-double-city-alberta': {'cost': 750,
                                               'name': "City network (AB) - double occupancy"},
                'confreg-2013-single-city-alberta': {'cost': 1050,
                                               'name': "City network (AB) - single occupancy"},
                'confreg-2013-nohotel-city-alberta': {'cost': 400,
                                               'name': "City network (AB) - no room"},

                'confreg-2013-quad-staff': {'cost': 0,
                                             'name': "EWB Staff - quad occupancy"},
                #'confreg-2013-double-staff': {'cost': 0,
                #                             'name': "EWB Staff - double occupancy"},
                #'confreg-2013-single-staff': {'cost': 0,
                #                             'name': "EWB Staff - single occupancy"},
                'confreg-2013-nohotel-staff': {'cost': 0,
                                             'name': "EWB Staff - no room"},

                #'confreg-2013-quad-alumni': {'cost': 350,
                #                             'name': "EWB Alumni"},
                #'confreg-2013-double-alumni': {'cost': 350,
                #                             'name': "EWB Alumni"},
                #'confreg-2013-single-alumni': {'cost': 350,
                #                             'name': "EWB Alumni"},
                #'confreg-2013-nohotel-alumni': {'cost': 350,
                #                             'name': "EWB Alumni"}
               
               }

ROOM_CHOICES = (('quad', _('Quad occupancy (four to a room)')),
                ('double', _('Double occupancy (two to a room)')),
                ('single', _('Single occupancy (private room)')),
                ('nohotel', _('Conference only (no hotel)'))                
               ) 
                
EXTERNAL_CHOICES = (('fridaystudent', _('Friday attendance (student)')),
                    ('saturdaystudent', _('Saturday attendance (student)')),
                    ('twodaystudent', _('Friday and Saturday attendance (student)')),
                    ('friday', _('Friday attendance')),
                    ('saturday', _('Saturday attendance')),
                    ('twoday', _('Friday and Saturday attendance'))
                   ) 
                
FINAL_CHOICES = (('friday', _('Friday attendance')),
                    ('saturday', _('Saturday attendance')),
                    ('twoday', _('Friday and Saturday attendance')),
                    ('fridaystudent', _('Friday attendance (student)')),
                    ('saturdaystudent', _('Saturday attendance (student)')),
                    ('twodaystudent', _('Friday and Saturday attendance (student)')),
                    ('nohotel', _('EWB member late registration (Thurs/Fri/Sat and gala - no hotel)')),
                   ) 
                

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
              )

AFRICA_FUND = (('75', 'Yes - $75'),
               ('45', 'Yes - $45'),
               ('20', 'Yes - $20'),
               ('other', 'Yes - other'),
               ('', 'No thank you'))

EXTERNAL_GROUPS = (('NGO member', 'NGO member'),
                   ('Engineering professional', 'Engineering professional'),
                   ('University student', 'University student'),
                   ('High school student', 'High school student'),
                   ('High school teacher', 'High school teacher'),
                   ('University professor / academia', 'University professor / academia'),
                   ('Government', 'Government'),
                   ('Other', 'Other'))

TSHIRT_CHOICES = (('n', 'No thanks'),
                  ('s', 'Small ($20)'),
                  ('m', 'Medium ($20)'),
                  ('l', 'Large ($20)'),
                  ('x', 'X-Large ($20)'))
                  
SKI_CHOICES = (('s', 'Students (14-21): $48'),
               ('a', 'Adults: $60'))
                  
ROLES_CHOICES = (('president', 'Chapter or City Network President'),
                 ('finance', 'Finance rep'),
                 ('advocacy', 'Advocacy rep'),
                 ('youth', 'Youth engagement rep'),
                 ('members', 'Member learning rep'),
                 ('communications', 'Communications rep'),
                 ('webmaster', 'Webmaster/online rep'),
                 ('fundraising', 'Fundraising rep'),
                 ('engineering', 'Global engineering rep'),
                 ('fairtrade', 'Fair Trade rep'),
                 ('otherexec', 'Other current exec role'),
                 ('pastjf', 'Past JF'),
                 ('currentjf', '2012 JF'),
                 ('alumni', 'Alumni'),
                 ('distributed', 'National distributed team member (past or present)'),
                 ('aps', 'APS (past or present)'),
                 ('office', 'National Office Staff or Social Change Fellow (past or present)'))
                 
CHAPTERTYPE_CHOICES = (('none', 'Not affiliated with a chapter'),
                       ('city', 'City network'),
                       ('enguni', 'University chapter - english'),
                       ('fruni', 'University chapter - french'))

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

