from django.utils.translation import ugettext_lazy as _
import settings

FOOD_CHOICES = (('none', _("no special preferences")),
                ('vegetarian', _("vegetarian")),
                ('vegan', _("vegan"))
    )

# this should be a dictionary, but needs to be a tuple to be used as an ENUM
CONF_CODES = (('a', "test"),
              ('b', "unifar"),
              ('c', "unimid"),
              ('d', "uniclose"),
              ('e', "staff"),
              ('f', "cityfar"),
              ('g', "citymid"),
              ('h', "cityclose"),
              ('i', "alumni"),
             )
              
CONF_CODES_LONG = (('a', "Test code"),
                   ('b', "University chapter (BC/AB/NL)"),
                   ('c', "University chapter (SK/MB/NB/NS)"),
                   ('d', "University chapter (ON/QB)"),
                   ('e', "EWB Staff"),
                   ('f', "City network (BC/AB/NL)"),
                   ('g', "City network (SK/MB/NB/NS)"),
                   ('h', "City network (ON/QB)"),
                   ('i', "EWB Alumni"),
                  )
              
CONF_HASH = settings.CONF_HASH
    
CONF_OPTIONS = {'confreg-2012-quad-test': {'cost': 175,
                                            'name': "Test - quad occupancy"},
                'confreg-2012-double-test': {'cost': 305,
                                            'name': "Test - double occupancy"},
                'confreg-2012-single-test': {'cost': 600,
                                            'name': "Test - single occupancy"},
                'confreg-2012-nohotel-test': {'cost': 140,
                                            'name': "Test - no room"},

                #'confreg-2012-quad-open': {'cost': 620,
                #                               'name': "Open registration (unsubsidized) - quad occupancy"},
                #'confreg-2012-double-open': {'cost': 740,
                #                               'name': "Open registration (unsubsidized) - double occupancy"},
                #'confreg-2012-single-open': {'cost': 990,
                #                               'name': "Open registration (unsubsidized) - single occupancy"},
                'confreg-2012-nohotel-open': {'cost': 425,
                                               'name': "Open registration (unsubsidized) - no room"},

#                'confreg-2012-friday-open': {'cost': 120,
#                                               'name': "Friday attendance"},
#                'confreg-2012-saturday-open': {'cost': 120,
#                                               'name': "Saturday attendance"},
#                'confreg-2012-twoday-open': {'cost': 220,
#                                               'name': "Friday/Saturday attendance"},
#                'confreg-2012-fridaystudent-open': {'cost': 60,
#                                               'name': "Friday attendance (student)"},
#                'confreg-2012-saturdaystudent-open': {'cost': 60,
#                                               'name': "Saturday attendance (student)"},
#                'confreg-2012-twodaystudent-open': {'cost': 110,
#                                               'name': "Friday/Saturday attendance (student)"},
#
#                'confreg-2012-friday-discounted': {'cost': 100,
#                                               'name': "Friday attendance (discounted)"},
#                'confreg-2012-saturday-discounted': {'cost': 100,
#                                               'name': "Saturday attendance (discounted)"},
#                'confreg-2012-twoday-discounted': {'cost': 180,
#                                               'name': "Friday/Saturday attendance (discounted)"},
#                'confreg-2012-fridaystudent-discounted': {'cost': 60,
#                                               'name': "Friday attendance (student)"},
#                'confreg-2012-saturdaystudent-discounted': {'cost': 60,
#                                               'name': "Saturday attendance (student)"},
#                'confreg-2012-twodaystudent-discounted': {'cost': 110,
#                                               'name': "Friday/Saturday attendance (student)"},
#
#                'confreg-2012-friday-friends': {'cost': 80,
#                                                'name': "Friday/Saturday attendance (friends)"},
#                'confreg-2012-saturday-friends': {'cost': 80,
#                                                'name': "Friday/Saturday attendance (friends)"},
#                'confreg-2012-twoday-friends': {'cost': 160,
#                                                'name': "Friday/Saturday attendance (friends)"},
#                'confreg-2012-fridaystudent-friends': {'cost': 60,
#                                               'name': "Friday attendance (student)"},
#                'confreg-2012-saturdaystudent-friends': {'cost': 60,
#                                               'name': "Saturday attendance (student)"},
#                'confreg-2012-twodaystudent-friends': {'cost': 110,
#                                               'name': "Friday/Saturday attendance (student)"},
#
#                'confreg-2012-friday-staff': {'cost': 0,
#                                                'name': "Friday/Saturday attendance (complimentary)"},
#                'confreg-2012-saturday-staff': {'cost': 0,
#                                                'name': "Friday/Saturday attendance (complimentary)"},
#                'confreg-2012-twoday-staff': {'cost': 0,
#                                                'name': "Friday/Saturday attendance (complimentary)"},
#                'confreg-2012-fridaystudent-staff': {'cost': 0,
#                                               'name': "Friday attendance (complimentary)"},
#                'confreg-2012-saturdaystudent-staff': {'cost': 0,
#                                               'name': "Saturday attendance (complimentary)"},
#                'confreg-2012-twodaystudent-staff': {'cost': 0,
#                                               'name': "Friday/Saturday attendance (complimentary)"},
                
                'confreg-2012-quad-unifar': {'cost': 125,
                                               'name': "University chapter (BC/AB/NL) - quad occupancy"},
                'confreg-2012-double-unifar': {'cost': 275,
                                               'name': "University chapter (BC/AB/NL) - double occupancy"},
                'confreg-2012-single-unifar': {'cost': 625,
                                               'name': "University chapter (BC/AB/NL) - single occupancy"},
                'confreg-2012-nohotel-unifar': {'cost': 80,
                                               'name': "University chapter (BC/AB/NL) - no room"},

                'confreg-2012-quad-unimid': {'cost': 225,
                                               'name': "University chapter (SK/MB/NB/NS) - quad occupancy"},
                'confreg-2012-double-unimid': {'cost': 375,
                                               'name': "University chapter (SK/MB/NB/NS) - double occupancy"},
                'confreg-2012-single-unimid': {'cost': 725,
                                               'name': "University chapter (SK/MB/NB/NS) - single occupancy"},
                'confreg-2012-nohotel-unimid': {'cost': 160,
                                               'name': "University chapter (SK/MB/NB/NS) - no room"},

                'confreg-2012-quad-uniclose': {'cost': 375,
                                               'name': "University chapter (ON/QB) - quad occupancy"},
                'confreg-2012-double-uniclose': {'cost': 525,
                                               'name': "University chapter (ON/QB) - double occupancy"},
                'confreg-2012-single-uniclose': {'cost': 875,
                                               'name': "University chapter (ON/QB) - single occupancy"},
                'confreg-2012-nohotel-uniclose': {'cost': 280,
                                               'name': "University chapter (ON/QB) - no room"},

                'confreg-2012-quad-cityfar': {'cost': 275,
                                               'name': "City network (BC/AB/NL) - quad occupancy"},
                'confreg-2012-double-cityfar': {'cost': 450,
                                               'name': "City network (BC/AB/NL) - double occupancy"},
                'confreg-2012-single-cityfar': {'cost': 785,
                                               'name': "City network (BC/AB/NL) - single occupancy"},
                'confreg-2012-nohotel-cityfar': {'cost': 200,
                                               'name': "City network (BC/AB/NL) - no room"},

                'confreg-2012-quad-citymid': {'cost': 375,
                                               'name': "City network (SK/MB/NB/NS) - quad occupancy"},
                'confreg-2012-double-citymid': {'cost': 550,
                                               'name': "City network (SK/MB/NB/NS) - double occupancy"},
                'confreg-2012-single-citymid': {'cost': 885,
                                               'name': "City network (SK/MB/NB/NS) - single occupancy"},
                'confreg-2012-nohotel-citymid': {'cost': 280,
                                               'name': "City network (SK/MB/NB/NS) - no room"},

                'confreg-2012-quad-cityclose': {'cost': 525,
                                               'name': "City network (ON/QB) - quad occupancy"},
                'confreg-2012-double-cityclose': {'cost': 700,
                                               'name': "City network (ON/QB) - double occupancy"},
                'confreg-2012-single-cityclose': {'cost': 1035,
                                               'name': "City network (ON/QB) - single occupancy"},
                'confreg-2012-nohotel-cityclose': {'cost': 320,
                                               'name': "City network (ON/QB) - no room"},

                'confreg-2012-quad-staff': {'cost': 0,
                                             'name': "EWB Staff - quad occupancy"},
                #'confreg-2012-double-staff': {'cost': 0,
                #                             'name': "EWB Staff - double occupancy"},
                #'confreg-2012-single-staff': {'cost': 0,
                #                             'name': "EWB Staff - single occupancy"},
                'confreg-2012-nohotel-staff': {'cost': 0,
                                             'name': "EWB Staff - no room"},

                #'confreg-2012-quad-alumni': {'cost': 350,
                #                             'name': "EWB Alumni"},
                #'confreg-2012-double-alumni': {'cost': 350,
                #                             'name': "EWB Alumni"},
                #'confreg-2012-single-alumni': {'cost': 350,
                #                             'name': "EWB Alumni"},
                'confreg-2012-nohotel-alumni': {'cost': 350,
                                             'name': "EWB Alumni"}
               
               }

ROOM_CHOICES = (('nohotel', _('Conference only (no hotel)')),
                ('quad', _('Quad occupancy (four to a room, shared beds)')),
                ('double', _('Double occupancy (two to a room, single beds)')),
                ('single', _('Single occupancy (private room)'))
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

ROLES_CHOICES_FR = (('president', 'Chapter or City Network President'),
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
                 
CHAPTERTYPE_CHOICES_FR = (('none', 'Not affiliated with a chapter'),
                       ('city', 'City network'),
                       ('enguni', 'University chapter - english'),
                       ('fruni', 'University chapter - french'))

