from datetime import date
from django import template
from django.template.defaultfilters import stringfilter
from django.core.urlresolvers import reverse
from django.forms.widgets import Select
from django.utils.translation import ugettext_lazy as _

register = template.Library()

@register.inclusion_tag("new_button.html")
def new_button(item, label=None):
  if label == None:
    label = item
  return {'label': label, 'item_url':reverse("%s_new" % item)}


# call {% select_box <choice_list>, <selected_value> %}
# <choice_list> and <selected_value> must be defined in the context
#
@register.tag(name="select_box")
def select_box(parser, token):
  bits = token.split_contents()
  if len(bits) < 2 or len(bits) > 3:
    raise template.TemplateSyntaxError, "%s tag requires one or two arguments" % bits[0]
  
  choice_list = bits[1]
  if len(bits) > 2:
    selected_item = bits[2]
  else:
    selected_item = None
  
  return SelectBox(choice_list, selected_item)

class SelectBox(template.Node):
  def __init__(self, choice_list, selected_item=None):
    self.choice_list = choice_list
    self.selected_item = selected_item
    
  def render(self, context):
    if context.has_key(self.choice_list):
      choice_list = context[self.choice_list]
    else:
      raise ValueError, "Can't find key %s in the context" % (self.choice_list)

    print "self.selected_item = %s" % (self.selected_item)

    if self.selected_item != None:
        if context.has_key(self.selected_item):
          selected_item = context[self.selected_item]
        else:
          raise ValueError, "Can't find key %s in the context" % (self.selected_item)
    else:
        selected_item = None

    return Select().render_options(choice_list, [selected_item])
    
# if the first date is newer than the second date, print "new".  duh.
# now, if django's templates supported "greater than" comparisons, I wouldn't need this...
@register.simple_tag
def isnewer(date1, date2):
    if date1 > date2:
        return _("new")
    else:
        return ""

# does a dictionary lookup, where the key is also a template variable
@register.tag()
def lookup(parser, token):
    try:
        tagname, dict, key = token.split_contents()
    except:
        raise template.TemplateSyntaxError, "%r tag takes exactly two arguments" % token.contents.split()[0]
    return LookupNode(dict, key)

class LookupNode(template.Node):
    def __init__(self, dict, key):
        self.dict = template.Variable(dict)
        self.key = template.Variable(key)
        
    def render(self, context):
        try:
            thedict = self.dict.resolve(context)
            thekey = self.key.resolve(context)
            
            # catch a KeyError, thrown if we were apssed a nested tuple instead of a dict
            value = None
            try:
                value = thedict[thekey]
            except:
                try:
                    dict2 = {}
                    for key, val in thedict:
                        dict2[key] = val
                    value = dict2[thekey]
                except:
                    pass
                
            return value
        except template.VariableDoesNotExist:
            return ''

# similar to lookup() as above, but inserts the value into the context intsead of printing it
@register.tag()
def lookup_ctx(parser, token):
    try:
        tagname, dict, key, astxt, variable = token.split_contents()
    except:
        raise template.TemplateSyntaxError, "%r tag takes exactly four arguments" % token.contents.split()[0]
#    return as_uni_form(LookupNode(dict, key))
    return LookupCtxNode(dict, key, variable)

class LookupCtxNode(template.Node):
    def __init__(self, dict, key, variable):
        self.dict = template.Variable(dict)
        self.key = template.Variable(key)
        self.variable = variable
        
    def render(self, context):
        try:
            thedict = self.dict.resolve(context)
            thekey = self.key.resolve(context)

            # catch a KeyError, thrown if we were apssed a nested tuple instead of a dict
            value = None
            try:
                value = thedict[thekey]
            except:
                try:
                    dict2 = {}
                    for key, val in thedict:
                        dict2[key] = val
                    value = dict2[thekey]
                except:
                    pass
                
            context[self.variable] = value
        except:
            pass
        return ''

@register.filter()
@stringfilter
def month(month):
    month = int(month)
    d = date(date.today().year, month, date.today().day)
    return d.strftime("%B")

@register.filter()
@stringfilter
def number_format(number):
    try:
        number = str(int(round(float(number))))
        count = commas = 0
        formatted = []
        for i in range(len(number) - 1, -1, -1):
            count += 1
            formatted.append(number[i])
            if count % 3 == 0 and i > 0:
                formatted.append(",")
        formatted.reverse()        
        return ''.join(formatted)
    except:
        return number

#s