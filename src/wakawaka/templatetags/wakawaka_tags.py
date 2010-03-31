# from http://open.e-scribe.com/browser/python/django/apps/protowiki/templatetags/wikitags.py
# copyright Paul Bissex, MIT license
import re
from django.template import Library
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse

from wakawaka import get_model
from wakawaka.urls import WIKI_SLUG

register = Library()

WIKI_WORDS_REGEX = re.compile(r'\b%s\b' % WIKI_SLUG)
wikipage_model = get_model()

@register.filter
def wikify(value):
    """Makes WikiWords"""
    def replace_wikiword(m):
        slug = m.group(1)
        try:
            page = wikipage_model.objects.get(slug=slug)
            return r'<a href="%s">%s</a>' % (reverse('wakawaka_page', kwargs={'slug': slug}), slug)
        except wikipage_model.ObjectDoesNotExist:
            return r'<a class="doesnotexist" href="%s">%s</a>' % (reverse('wakawaka_edit', kwargs={'slug': slug}), slug)

    return mark_safe(WIKI_WORDS_REGEX.sub(replace_wikiword, value))
