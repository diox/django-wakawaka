from django.contrib import admin

from wakawaka import get_model
from wakawaka.models import WikiPage, Revision

class RevisionInlines(admin.TabularInline):
    model = Revision
    extra = 1

class WikiPageAdmin(admin.ModelAdmin):
    inlines = [RevisionInlines]

class RevisionAdmin(admin.ModelAdmin):
    pass

# Only register the default admin if the model is the built-in wiki model
# (this won't be true if there's a custom wiki app).
if get_model() is WikiPage:
    admin.site.register(WikiPage, WikiPageAdmin)
admin.site.register(Revision, RevisionAdmin)