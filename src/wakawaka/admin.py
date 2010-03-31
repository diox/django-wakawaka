from django.contrib import admin

from wakawaka import get_wikipage_model, get_revision_model
from wakawaka.models import WikiPage, Revision

class RevisionInlines(admin.TabularInline):
    model = Revision
    extra = 1

class WikiPageAdmin(admin.ModelAdmin):
    inlines = [RevisionInlines]

class RevisionAdmin(admin.ModelAdmin):
    pass

# Only register the default admin if models are built-in models
# (this won't be true if there's a custom wiki app).
if get_wikipage_model() is WikiPage:
    admin.site.register(WikiPage, WikiPageAdmin)
if get_revision_model() is Revision:
    admin.site.register(Revision, RevisionAdmin)