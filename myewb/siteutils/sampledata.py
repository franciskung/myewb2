# description = models.TextField()
# longterm = models.BooleanField()
# deleted = models.BooleanField(default=False)
# start_date = models.DateField(null=True)
# end_date = models.DateField(null=True)
# country = CountryField(ewb='placements')
# town = models.CharField(max_length=100)
# flight_request_made = models.BooleanField(default=True)
# 
# sector = models.ForeignKey(Sector)
# coach = models.ForeignKey(User, related_name=_('coach'))
# user = models.ForeignKey(User, null=True, related_name=_('user'))

# Country LastName  FirstName  Location  Arrival Departure Phone number  Partner Sector Team Return flight date (as per latest booking)  Blog Address  From what chapter?

from django.contrib.auth.models import User
from pinax.apps.profiles.models import Profile
from volunteering.models import Placement
from volunteering.models import Sector

from siteutils.countries import COUNTRIES, REVERSE_COUNTRY_MAP
import time

def cleardata():
  for p in User.objects.all()[1:]:
    p.delete()

  for p in Profile.objects.all()[1:]:
    p.delete()

  for p in Placement.objects.all():
    p.delete()

def loaddata():
  data = open("/Users/paul/ov-sheet.txt").read().split("\n")[:-1]

  for d in data:
      # (country, last, first, town, start, end, phone, partner, sector_team, return_flight, blog_url, chapter_name)
      line  = d.split("\t")
      country = line[0]
      last = line[1]
      first = line[2]
      town = line[3]
      start = line[4]
      end = line[5]
    
      if (len(line) > 7):
        partner = line[7]
      else:
        partner = ""

      if (len(line) > 8):
        sector_team = line[8]
      else:
        sector_team = ""

      if len(start):
        start_date = time.strftime("%Y-%m-%d", time.strptime(start, "%m/%d/%Y"))
      else:
        start_date = None
      
      if len(end):
        end_date = time.strftime("%Y-%m-%d", time.strptime(end, "%m/%d/%Y"))
      else:
        end_date = None
    
      if len(sector_team):
        sector = Sector.objects.get(name=sector_team)
      else:
        sector = None

      print "Adding %s %s" % (first, last)
      print "start_date=%s, end_date=%s, town=%s, sector=%s" % (start_date, end_date, town, sector)

      if REVERSE_COUNTRY_MAP.has_key(country):
        country = REVERSE_COUNTRY_MAP[country]

        print "Adding %s %s" % (first, last)
        print "start_date=%s, end_date=%s, country=%s, town=%s, sector=%s" % (start_date, end_date, country, town, sector)

        u = User.objects.create_user(first + "." + last, 'dummy@ewb.ca', 'password')
        p = u.get_profile()
        p.last_name=last
        p.first_name=first
        p.save()
    

        Placement.objects.create(profile=p, start_date=start_date, end_date=end_date, country=country, town=town, sector=sector)
