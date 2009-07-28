from django import template
from django.utils.encoding import smart_str
from django.core.urlresolvers import reverse, NoReverseMatch


register = template.Library()


class GroupURLNode(template.Node):
    def __init__(self, view_name, group, args, kwargs, asvar):
        self.view_name = view_name
        self.group = group
        self.kwargs = kwargs
        self.asvar = asvar
    
    def render(self, context):
        group = self.group.resolve(context)
        bridge = group.content_bridge
        
        kwargs = {}
        for k, v in self.kwargs.items():
            kwargs[smart_str(k, "ascii")] = v.resolve(context)
        
        try:
            url = bridge.reverse(self.view_name, group, kwargs=kwargs)
        except NoReverseMatch:
            try:
                url = reverse(self.view_name, kwargs=kwargs)
            except NoReverseMatch:
                if self.asvar is None:
                    raise
        
        if self.asvar:
            context[self.asvar] = url
            return ""
        else:
            return url


@register.tag
def groupurl(parser, token):
    bits = token.contents.split()
    if len(bits) < 3:
        raise template.TemplateSyntaxError("'%s' takes at least two arguments"
            " (path to a view and a group)" % bits[0])
    
    view_name = bits[1]
    group = parser.compile_filter(bits[2])
    args = []
    kwargs = {}
    asvar = None
    
    if len(bits) > 3:
        bits = iter(bits[3:])
        for bit in bits:
            if bit == "as":
                asvar = bits.next()
                break
            else:
                for arg in bit.split(","):
                    if "=" in arg:
                        k, v = arg.split("=", 1)
                        k = k.strip()
                        kwargs[k] = parser.compile_filter(v)
                    elif arg:
                        args.append(parser.compile_filter(arg))
    
    return GroupURLNode(view_name, group, [], kwargs, asvar)
