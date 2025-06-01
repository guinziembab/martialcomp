# permissions_manager/templatetags/permissions_tags.py

from django import template
from django.template.base import token_kwargs
from ..auth import user_has_permission, get_user_roles

register = template.Library()

@register.simple_tag(takes_context=True)
def has_permission(context, permission_code, obj=None):
    """
    Vérifie si l'utilisateur actuel a une permission donnée

    Usage: {% has_permission 'edit_club' club as can_edit %}
    """
    user = context['request'].user
    return user_has_permission(user, permission_code, obj)

@register.inclusion_tag('permissions_manager/show_roles.html', takes_context=True)
def show_user_roles(context, obj=None):
    """
    Affiche les rôles de l'utilisateur actuel

    Usage: {% show_user_roles %}
           {% show_user_roles federation %}
    """
    user = context['request'].user
    roles = get_user_roles(user, obj)
    return {
        'roles': roles,
        'context_name': str(obj) if obj else 'Global'
    }

class ShowIfPermittedNode(template.Node):
    def __init__(self, nodelist_true, nodelist_false, permission_code, obj=None):
        self.nodelist_true = nodelist_true
        self.nodelist_false = nodelist_false
        self.permission_code = template.Variable(permission_code)
        self.obj = template.Variable(obj) if obj else None

    def render(self, context):
        try:
            permission_code = self.permission_code.resolve(context)
            obj = self.obj.resolve(context) if self.obj else None
            user = context['request'].user
            
            if user_has_permission(user, permission_code, obj):
                return self.nodelist_true.render(context)
            else:
                return self.nodelist_false.render(context) if self.nodelist_false else ''
        except template.VariableDoesNotExist:
            return ''

@register.tag('show_if_permitted')
def do_show_if_permitted(parser, token):
    """
    Affiche contenu uniquement si l'utilisateur a la permission

    Usage: {% show_if_permitted 'create_competition' club %}
            <a href="...">Créer une compétition</a>
           {% else %}
            <span class="disabled">Créer une compétition</span>
           {% endshow_if_permitted %}
    """
    bits = token.split_contents()
    if len(bits) < 2:
        raise template.TemplateSyntaxError(f"'{bits[0]}' takes at least one argument, the permission code.")
    
    permission_code = bits[1]
    obj = bits[2] if len(bits) > 2 else None
    
    nodelist_true = parser.parse(('else', 'endshow_if_permitted'))
    token = parser.next_token()
    
    if token.contents == 'else':
        nodelist_false = parser.parse(('endshow_if_permitted',))
        parser.delete_first_token()
    else:
        nodelist_false = None
    
    return ShowIfPermittedNode(nodelist_true, nodelist_false, permission_code, obj)