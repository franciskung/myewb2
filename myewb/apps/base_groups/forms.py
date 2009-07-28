from django import forms
from django.utils.translation import ugettext_lazy as _

from base_groups.models import BaseGroup, GroupMember, GroupLocation

# @@@ we should have auto slugs, even if suggested and overrideable

class BaseGroupForm(forms.ModelForm):
    
    slug = forms.SlugField(max_length=20,
        help_text = _("a short version of the name consisting only of letters, numbers, underscores and hyphens."),
        error_message = _("This value must contain only letters, numbers, underscores and hyphens."))
            
    def clean_slug(self):
        model = self.Meta.model
        if model.objects.filter(slug__iexact=self.cleaned_data["slug"]).count() > 0:
            raise forms.ValidationError(_("A %s already exists with that slug.") % model)
        return self.cleaned_data["slug"].lower()
    
    def clean_name(self):
        model = self.Meta.model
        if model.objects.filter(name__iexact=self.cleaned_data["name"]).count() > 0:
            raise forms.ValidationError(_("A %s already exists with that name.") % model)
        return self.cleaned_data["name"]
    
    class Meta:
        model = BaseGroup
        fields = ('name', 'slug', 'description')


# @@@ is this the right approach, to have two forms where creation and update fields differ?

# class BaseGroupUpdateForm(forms.ModelForm):
#     
#     def clean_name(self):
#         model = self.Meta.model
#         if model.objects.filter(name__iexact=self.cleaned_data["name"]).count() > 0:
#             if self.cleaned_data["name"] == self.instance.name:
#                 pass # same instance
#             else:
#                 raise forms.ValidationError(_("A %s already exists with that name.") % model)
#         return self.cleaned_data["name"]
#     
#     class Meta:
#         model = BaseGroup
#         fields = ('name', 'description')

class GroupMemberForm(forms.ModelForm):

    class Meta:
        model = GroupMember
        fields = ('user', 'is_admin', 'admin_title')
        
class GroupLocationForm(forms.ModelForm):
    
    class Meta:
        model = GroupLocation
        fields = ('place', 'latitude', 'longitude')
