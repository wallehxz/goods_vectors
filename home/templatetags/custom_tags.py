from django import template

register = template.Library()


@register.simple_tag
def safe_get(dictionary, key, default=""):
    return dictionary.get(str(key), default)


@register.simple_tag
def media_url_path(full_path):
    return f'media{full_path.split("media")[-1]}'


@register.simple_tag
def pdd_price(price):
    return f"￥：{int(price) / 100}"
