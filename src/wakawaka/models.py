from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User

from wakawaka import get_model

class BaseWikiPage(models.Model):
    """
    An abstract base class that any custom wikipage models probably should
    subclass.
    """
    slug = models.CharField(_('slug'), max_length=255)

    class Meta:
        abstract = True
        ordering = ['slug']

    def __unicode__(self):
        return self.slug

    @property
    def current(self):
        return self.revisions.latest()

    @property
    def rev(self, rev_id):
        return self.revisions.get(pk=rev_id)


class WikiPage(BaseWikiPage):
    """
    A Wiki page.
    """
    created = models.DateTimeField(_('created'), auto_now_add=True)
    modified = models.DateTimeField(_('modified'), auto_now=True)


class Revision(models.Model):
    page = models.ForeignKey(get_model(), related_name='revisions')
    content = models.TextField(_('content'))
    message = models.TextField(_('change message'), blank=True)
    creator = models.ForeignKey(User, blank=True, null=True)
    creator_ip = models.IPAddressField(_('creator ip'))
    created = models.DateTimeField(_('created'), auto_now_add=True)
    modified = models.DateTimeField(_('modified'), auto_now=True)

    class Meta:
        ordering = ['-modified']
        get_latest_by = 'modified'

    def __unicode__(self):
        return 'Revision %s for %s' % (self.created.strftime('%Y%m%d-%H%M'), self.page.slug)