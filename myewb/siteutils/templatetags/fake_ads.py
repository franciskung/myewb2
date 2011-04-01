from django.template import Context, loader
from django import template

import settings
import os
from random import choice

register = template.Library()

@register.simple_tag
def fake_ad():
    templatedir = os.path.join(settings.PROJECT_ROOT, "templates", "fake_ads")
    ads = os.listdir(templatedir)
    adname = choice(ads)

    context = {'STATIC_URL': settings.STATIC_URL}
    ad = loader.get_template("fake_ads/%s" % adname).render(Context(context))
    
    return ad

