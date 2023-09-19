from django import template

register = template.Library()


@register.filter
def get_item_from_dict(dictionary, key):
    # Return an empty string if the key is not found
    return dictionary.get(key, '')
