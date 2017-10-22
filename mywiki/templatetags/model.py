from django import template
from mywiki.models import *
from django.contrib.auth.models import User


register = template.Library()

@register.filter
def get_model(value, name):
    return eval(name + '.objects.get(pk=' + str(value) + ')')
    
@register.filter
def get_attribute(value, attribute):
    return getattr(value, attribute)