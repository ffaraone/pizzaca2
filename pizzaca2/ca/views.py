import os
import logging

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import ugettext as _
from django.conf import settings
from django.contrib.auth.decorators import user_passes_test

from haystack.inputs import AutoQuery
from haystack.query import SearchQuerySet, SQ

from ..engine import openssl
from .forms import CAForm, SubCAForm
from .models import CA, SubCA


logger = logging.getLogger(__name__)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def ca_search(request):
    cas = None
    query = request.GET.get('q', '')
    page = request.GET.get('page', 1)

    flt = SQ()

    if query:
        flt &= SQ(content=AutoQuery(query))

    cas = SearchQuerySet().filter(flt).models(CA).order_by('-last_modified')

    paginator = Paginator(cas, 5)

    try:
        cas_list = paginator.page(page)
    except PageNotAnInteger:
        cas_list = paginator.page(1)
    except EmptyPage:
        cas_list = paginator.page(paginator.num_pages)
    return render(
        request,
        'ca/ca_search.html',
        {
            'objects_page': cas_list,
            'query': query
        }
    )


@login_required
@user_passes_test(lambda u: u.is_superuser)
def ca_create(request):
    if not request.user.is_superuser:
        raise
    f = CAForm(request.POST or None)
    if f.is_valid():
        instance = f.save(commit=False)
        instance.save()
        messages.success(request,
                         _('The new certification authority %s '
                           'has been saved successfully') % instance.CN)
        return redirect('ca:ca_search')
    return render(request, 'ca/ca_edit.html', {'f': f})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def ca_update(request, pk):
    ca = get_object_or_404(CA, pk=pk)
    f = CAForm(request.POST or None, instance=ca)
    if f.is_valid():
        f.save()
        return redirect('ca:ca_search')
    return render(request, 'ca/ca_edit.html', {'f': f})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def ca_generate(request, pk):
    ca = get_object_or_404(CA, pk=pk)
    if ca.status != 'new':
        messages.error(
            request, _('The root certificate for %s '
                       'has already been generated') % ca.CN)
        return redirect('ca:ca_search')
    try:
        (not_before, not_after) = openssl.create_stdroot(pk, ca.CN,
                                                         ca.O, ca.OU, ca.C)
        ca.status = 'active'
        ca.not_before = not_before
        ca.not_after = not_after
        ca.save()
        messages.success(
            request, _('The root certificate for %s '
                       'has been generated successfully') % ca.CN)
        return redirect('ca:ca_search')
    except:
        logger.exception('cannot generate root ca cert')
        messages.error(
            request, _('The root certificate for %s '
                       'cannot be generated. '
                       'openssl returns an error.') % ca.CN)
        return redirect('ca:ca_search')


def ca_get_resource(request, pk, res):
    if res[-3:] == 'crl':
        with open(os.path.join(settings.CA_ROOT, 'stdroot', str(pk), 'ca',
                  'crl', res)) as f:
            data = f.read()
        return HttpResponse(data, content_type='application/pkix-crl')
    else:
        with open(os.path.join(settings.CA_ROOT, 'stdroot', str(pk), 'ca',
                  res)) as f:
            data = f.read()
        return HttpResponse(data, content_type='application/x-x509-ca-cert')


@login_required
@user_passes_test(lambda u: u.is_superuser)
def subca_search(request):
    cas = None
    query = request.GET.get('q', '')
    page = request.GET.get('page', 1)

    flt = SQ()

    if query:
        flt &= SQ(content=AutoQuery(query))

    cas = SearchQuerySet().filter(flt).models(SubCA)

    paginator = Paginator(cas, 5)

    try:
        cas_list = paginator.page(page)
    except PageNotAnInteger:
        cas_list = paginator.page(1)
    except EmptyPage:
        cas_list = paginator.page(paginator.num_pages)

    return render(
        request,
        'ca/subca_search.html',
        {
            'objects_page': cas_list,
            'query': query
        }
    )


@login_required
@user_passes_test(lambda u: u.is_superuser)
def subca_create(request):
    f = SubCAForm(request.POST or None)
    if f.is_valid():
        instance = f.save(commit=False)
        instance.save()
        f.save_m2m()
        messages.success(request,
                         _('The new certification authority %s '
                           'has been saved successfully') % instance.CN)
        return redirect('ca:subca_search')
    return render(request, 'ca/subca_edit.html', {'f': f})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def subca_update(request, pk):
    ca = get_object_or_404(SubCA, pk=pk)
    f = SubCAForm(request.POST or None, instance=ca)
    if f.is_valid():
        f.save()
        return redirect('ca:subca_search')
    return render(request, 'ca/subca_edit.html', {'f': f})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def subca_operators(request, pk):
    ca = get_object_or_404(SubCA, pk=pk)
    if request.POST:
        operators = request.POST.getlist('operators')
        # add non-existent
        for op in operators:
            if not ca.operators.filter(pk=int(op)).exists():
                ca.operators.add(get_user_model().objects.get(pk=int(op)))
        for op in ca.operators.all():
            if not str(op.pk) in operators:
                ca.operators.remove(op)
        ca.save()
        messages.success(request, _('Operators modified successfully'))
        return redirect('ca:subca_search')

    operators = get_user_model().objects.filter(is_superuser=False,
                                                is_active=True)
    selected_operators = [u.pk for u in ca.operators.all()]
    return render(
        request,
        'ca/subca_users.html',
        {
            'subca_id': ca.pk,
            'subca_name': unicode(ca),
            'operators': operators,
            'selected_operators': selected_operators
        }
    )


def subca_get_resource(request, pk, res):
    if res[-3:] == 'crl':
        with open(os.path.join(settings.CA_ROOT, 'stdsub', str(pk), 'ca',
                  'crl', res)) as f:
            data = f.read()
        return HttpResponse(data, content_type='application/pkix-crl')
    else:
        with open(os.path.join(settings.CA_ROOT, 'stdsub', str(pk), 'ca',
                  res)) as f:
            data = f.read()
        return HttpResponse(data, content_type='application/x-x509-ca-cert')


@login_required
@user_passes_test(lambda u: u.is_superuser)
def subca_generate(request, pk):
    subca = get_object_or_404(SubCA, pk=pk)
    if subca.status != 'new':
        messages.error(
            request, _('The root certificate for %s '
                       'has already been generated') % subca.CN)
        return redirect('ca:subca_search')
    try:
        (not_before, not_after) = openssl.create_stdsub(
            pk, subca.kind,
            subca.ca.pk, subca.CN,
            subca.ca.O, subca.OU, subca.ca.C)
        subca.status = 'active'
        subca.not_before = not_before
        subca.not_after = not_after
        subca.save()
        messages.success(
            request, _('The root certificate for %s '
                       'has been generated successfully') % subca.CN)
        return redirect('ca:subca_search')
    except Exception as e:
        messages.error(
            request, _('The root certificate for %s '
                       'cannot be generated. '
                       'openssl returns an error. (%s)') % (subca.CN, e))
        return redirect('ca:subca_search')


def ca_generate_crl(request):
    try:
        cas = CA.objects.all()
        for ca in cas:
            openssl.gencrl_root(ca.pk)
        return HttpResponse('OK')
    except Exception as e:
        messages.error(
            request, _('A ca crl cannot be generated.'))
        raise e


def subca_generate_crl(request):
    try:
        subcas = SubCA.objects.all()
        for subca in subcas:
            openssl.gencrl_stdsub(subca.pk, subca.kind)
        return HttpResponse('OK')
    except Exception as e:
        messages.error(
            request, _('A subca crl cannot be generated.'))
        raise e
