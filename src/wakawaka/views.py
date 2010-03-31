import difflib
from django.conf import settings
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from django.http import HttpResponseRedirect, HttpResponseBadRequest,\
    HttpResponseForbidden, Http404
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext, ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist

from wakawaka import get_wikipage_model, get_revision_model, get_wiki_app_name
from wakawaka.forms import WikiPageForm, DeleteWikiPageForm

__all__ = ['index', 'page', 'edit', 'revisions', 'changes', 'revision_list', 'page_list']

wiki_app_name = get_wiki_app_name()
revision_model = get_revision_model()
wikipage_model = get_wikipage_model()
revision_model_name = revision_model.__name__.lower()
wikipage_model_name = wikipage_model.__name__.lower()

def index(request, template_name='wakawaka/page.html', extra_context={}):
    '''
    Redirects to the default wiki index name.
    '''
    index_slug = getattr(settings, 'WAKAWAKA_DEFAULT_INDEX', 'WikiIndex')
    return HttpResponseRedirect(reverse('wakawaka_page', kwargs={'slug': index_slug}))

def page(request, slug, rev_id=None, template_name='wakawaka/page.html', extra_context={}):
    '''
    Displays a wiki page. Redirects to the edit view if the page doesn't exist.
    '''
    try:
        page = wikipage_model.objects.get(slug=slug)
        rev = page.current

        # Display an older revision if rev_id is given
        if rev_id:
            rev_specific = revision_model.objects.get(pk=rev_id)
            if rev.pk != rev_specific.pk:
                rev_specific.is_not_current = True
            rev = rev_specific

    # The Page does not exist, redirect to the edit form or
    # deny, if the user has no permission to add pages
    except wikipage_model.DoesNotExist:
        if request.user.is_authenticated():
            return HttpResponseRedirect(reverse('wakawaka_edit', kwargs={'slug': slug}))
        raise Http404

    template_context = {
        'page': page,
        'rev': rev,
    }
    template_context.update(extra_context)
    return render_to_response(template_name, template_context,
                              RequestContext(request))

def edit(request, slug, rev_id=None, template_name='wakawaka/edit.html', extra_context={},
         wiki_page_form=WikiPageForm, wiki_delete_form=DeleteWikiPageForm):
    '''
    Displays the form for editing and deleting a page.
    '''

    # Get the page for slug and get a specific revision, if given
    try:
        page = wikipage_model.objects.get(slug=slug)
        rev = page.current
        initial = {'content': page.current.content}

        # Do not allow editing wiki pages if the user has no permission
        if not request.user.has_perms(('%s.change_%s' % (wiki_app_name, wikipage_model_name), 
                                       '%s.change_%s' % (wiki_app_name, revision_model_name))):
            return HttpResponseForbidden(ugettext('You don\'t have permission to edit pages.'))

        if rev_id:
            # There is a specific revision, fetch this
            rev_specific = revision_model.objects.get(pk=rev_id)
            if rev.pk != rev_specific.pk:
                rev = rev_specific
                rev.is_not_current = True
                initial = {'content': rev.content, 'message': _('Reverted to "%s"' % rev.message)}


    # This page does not exist, create a dummy page
    # Note that it's not saved here
    except wikipage_model.DoesNotExist:

        # Do not allow adding wiki pages if the user has no permission
        if not request.user.has_perms(('%s.add_%s' % (wiki_app_name, wikipage_model_name), 
                                       '%s.add_%s' % (wiki_app_name, revision_model_name))):
            return HttpResponseForbidden(ugettext('You don\'t have permission to add wiki pages.'))

        page = wikipage_model(slug=slug)
        page.is_initial = True
        rev = None
        initial = {'content': _('Describe your new page %s here...' % slug),
                   'message': _('Initial revision')}

    # Don't display the delete form if the user has nor permission
    delete_form = None
    # The user has permission, then do
    if request.user.has_perm('%s.delete_%s' % (wiki_app_name, wikipage_model_name)) or \
       request.user.has_perm('%s.delete_%s' % (wiki_app_name, revision_model_name)):
        delete_form = wiki_delete_form(request)
        if request.method == 'POST' and request.POST.get('delete'):
            delete_form = wiki_delete_form(request, request.POST)
            if delete_form.is_valid():
                return delete_form.delete_wiki(request, page, rev)

    # Page add/edit form
    form = wiki_page_form(initial=initial)
    if request.method == 'POST':
        form = wiki_page_form(data=request.POST)
        if form.is_valid():
            # Check if the content is changed, except there is a rev_id and the
            # user possibly only reverted the HEAD to it
            if not rev_id and initial['content'] == form.cleaned_data['content']:
                form.errors['content'] = (_('You have made no changes!'),)

            # Save the form and redirect to the page view
            else:
                try:
                    # Check that the page already exist
                    page = wikipage_model.objects.get(slug=slug)
                except wikipage_model.DoesNotExist:
                    # Must be a new one, create that page
                    page = wikipage_model.objects.create(slug=slug)

                form.save(request, page)

                request.user.message_set.create(message=ugettext('Your changes to %s were saved' % page.slug))
                return HttpResponseRedirect(reverse('wakawaka_page', kwargs={'slug': page.slug}))

    template_context = {
        'form': form,
        'delete_form': delete_form,
        'page': page,
        'rev': rev,
    }
    template_context.update(extra_context)
    return render_to_response(template_name, template_context,
                              RequestContext(request))

def revisions(request, slug, template_name='wakawaka/revisions.html',
                  extra_context={}):
    '''
    Displays the list of all revisions for a specific wikipage_model
    '''

    page = get_object_or_404(wikipage_model, slug=slug)
    template_context = {
        'page': page,
    }
    template_context.update(extra_context)
    return render_to_response(template_name, template_context,
                              RequestContext(request))

def changes(request, slug, template_name='wakawaka/changes.html', extra_context={}):
    '''
    Displays the changes between two revisions.
    '''
    rev_a_id = request.GET.get('a', None)
    rev_b_id = request.GET.get('b', None)

    # Some stinky fingers manipulated the url
    if not rev_a_id or not rev_b_id:
        return HttpResponseBadRequest('Bad Request')

    try:
        rev_a = revision_model.objects.get(pk=rev_a_id)
        rev_b = revision_model.objects.get(pk=rev_b_id)
        page = wikipage_model.objects.get(slug=slug)
    except ObjectDoesNotExist:
        raise Http404

    if rev_a.content != rev_b.content:
        d = difflib.unified_diff(rev_b.content.splitlines(),
                                 rev_a.content.splitlines(),
                                 'Original', 'Current', lineterm='')
        difftext = '\n'.join(d)
    else:
        difftext = _(u'No changes were made between this two files.')

    template_context = {
        'page': page,
        'diff': difftext,
        'rev_a': rev_a,
        'rev_b': rev_b,
    }
    template_context.update(extra_context)
    return render_to_response(template_name, template_context,
                              RequestContext(request))

# Some useful views
def revision_list(request, template_name='wakawaka/revision_list.html', extra_context={}):
    '''
    Displays a list of all recent revisions.
    '''
    template_context = {
        'revision_list': revision_model.objects.all(),
    }
    template_context.update(extra_context)
    return render_to_response(template_name, template_context,
                              RequestContext(request))

def page_list(request, template_name='wakawaka/page_list.html', extra_context={}):
    '''
    Displays all Pages
    '''
    template_context = {
        'page_list': wikipage_model.objects.order_by('slug'),
        'index_slug': getattr(settings, 'WAKAWAKA_DEFAULT_INDEX', 'WikiIndex'),
    }
    template_context.update(extra_context)
    return render_to_response(template_name, template_context,
                              RequestContext(request))