from django import template
from django.forms import BaseForm
from django.utils.translation import gettext, gettext_lazy as _

register = template.Library()


@register.filter(name='boolean_localize')
def boolean_localize(boolean:bool):
    if boolean:
        return _('是')
    else:
        return _('否')
