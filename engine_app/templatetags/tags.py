from django import template

register = template.Library()

@register.filter
def select_item(queryset,i):
    return queryset[i]