from django import template
from mywiki.models import *
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist


register = template.Library()

@register.filter
def get_model(value, name):
    return eval(name + '.objects.get(pk=' + str(value) + ')')
    
@register.filter
def get_attribute(value, attribute):
    return getattr(value, attribute)
    
@register.filter
def get_revision(title):
    try:
        page = Page.objects.get(title=title, is_created=True)
    except ObjectDoesNotExist:
        return False
    return Revision.objects.filter(page=page.id).order_by('-id').first()