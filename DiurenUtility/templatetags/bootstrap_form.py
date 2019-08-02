from django import template
from django.forms import BaseForm
from django.utils.translation import gettext, gettext_lazy as _

register = template.Library()


@register.filter(name='bootstrap_form')
def bootstrap_form(form: BaseForm):
    if not issubclass(form.__class__, BaseForm):
        raise ValueError(_('本模板标签不能用于%s。') % form.__class__)
    form.required_css_class = 'font-weight-bold'
    form.error_css_class = 'text-danger'
    for field_name in form.fields:
        form.fields[field_name].widget.attrs.update(
            {'class': 'form-control',
             'placeholder': _('请输入%s') % form.fields[field_name].label})
    return form
