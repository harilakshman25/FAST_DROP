from django import template

register = template.Library()

@register.filter
def has_role(user, role):
    return hasattr(user, 'role') and user.role == role 