from django.conf import settings
from django.core import urlresolvers
from django.core.exceptions import ImproperlyConfigured
from django.utils.importlib import import_module


DEFAULT_WIKI_APP = 'wakawaka'

def get_wiki_app():
    """
    Get the iki app (i.e. "wakawaka") as defined in the settings
    """
    # Make sure the app's in INSTALLED_APPS
    wiki_app = get_wiki_app_name()
    if wiki_app not in settings.INSTALLED_APPS:
        raise ImproperlyConfigured("The WIKI_APP (%r) "\
                                   "must be in INSTALLED_APPS" % settings.WIKI_APP)

    # Try to import the package
    try:
        package = import_module(wiki_app)
    except ImportError:
        raise ImproperlyConfigured("The WIKI_APP setting refers to "\
                                   "a non-existing package.")

    return package

def get_wiki_app_name():
    """
    Returns the name of the wiki app (either the setting value, if it
    exists, or the default).
    """
    return getattr(settings, 'WIKI_APP', DEFAULT_WIKI_APP)

def get_wikipage_model():
    """
    Returns the wikipage model class.
    """
    if get_wiki_app_name() != DEFAULT_WIKI_APP and hasattr(get_wiki_app(), "get_wikipage_model"):
        return get_wiki_app().get_wikipage_model()
    else:
        from wakawaka.models import WikiPage
        return WikiPage

def get_revision_model():
    """
    Returns the revision model class.
    """
    if get_wiki_app_name() != DEFAULT_WIKI_APP and hasattr(get_wiki_app(), "get_revision_model"):
        return get_wiki_app().get_revision_model()
    else:
        from wakawaka.models import Revision
        return Revision
    