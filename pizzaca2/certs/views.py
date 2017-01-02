from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _
from haystack.inputs import AutoQuery
from haystack.query import SQ, SearchQuerySet
from OpenSSL import crypto

import logging

from ..ca.models import SubCA
from ..engine import openssl
from .forms import IdentityForm, ServerForm
from .models import CRL_REASON_CHOICES, Identity, Server

logger = logging.getLogger(__name__)

@login_required
@permission_required('certs.can_search_identity')
def identity_search(request):
    ids = None
    query = request.GET.get('q', '')
    page = request.GET.get('page', 1)

    flt = SQ()

    if not request.user.is_superuser:
        flt &= SQ(issuer_operators=request.user.pk)

    if query:
        flt &= SQ(content=AutoQuery(query))

    ids = SearchQuerySet().filter(flt).models(Identity) \
        .order_by('-last_modified')

    paginator = Paginator(ids, 5)

    try:
        ids_list = paginator.page(page)
    except PageNotAnInteger:
        ids_list = paginator.page(1)
    except EmptyPage:
        ids_list = paginator.page(paginator.num_pages)
    return render(
        request,
        'certs/identity_search.html',
        {
            'objects_page': ids_list,
            'query': query,
            'crl_reasons': CRL_REASON_CHOICES
        }
    )


@login_required
@permission_required('certs.add_identity')
def identity_create(request):
    f = IdentityForm(request.user, request.POST or None)
    if f.is_valid():
        instance = f.save(commit=False)
        instance.save()
        messages.success(request,
                         _('The certificate request for %s '
                           'has been saved successfully.') % instance.CN)
        return redirect('certs:identity_search')
    return render(request, 'certs/identity_edit.html', {'f': f})


@login_required
@permission_required('certs.change_identity')
def identity_update(request, pk):
    identity = get_object_or_404(Identity, pk=pk)
    if identity.status != 'new':
        messages.error(request,
                         _('The certificate request for %s '
                           'cannot be updated: invalid status.') % identity.CN)
        return redirect('certs:identity_search')
    f = IdentityForm(request.user, request.POST or None, instance=identity)
    if f.is_valid():
        f.save()
        return redirect('certs:identity_search')
    return render(request, 'certs/identity_edit.html', {'f': f})


@login_required
@permission_required('certs.delete_identity')
def identity_delete(request):
    if not 'pk' in request.POST:
        raise Exception('pk not provided!')
    pk = request.POST['pk']
    identity = get_object_or_404(Identity, pk=int(pk))
    if identity.status != 'new':
        messages.error(request,
                         _('The certificate request for %s '
                           'cannot be deleted: invalid status.') % identity.CN)
        return redirect('certs:identity_search')
    identity.delete()
    messages.success(request,
                     _('The certificate request for  %s '
                       'has been deleted successfully') % identity.CN)
    return redirect('certs:identity_search')


@login_required
@permission_required('certs.can_generate_identity')
def identity_generate(request, pk):
    identity = get_object_or_404(Identity, pk=pk)
    if identity.status == 'new':
        try:
            if identity.cert_format == 'P12':
                openssl.gencsr_identity(
                    identity.issuer.pk,
                    identity.pk,
                    identity.CN,
                    identity.T,
                    identity.GN,
                    identity.SN,
                    identity.E,
                    identity.O,
                    identity.OU,
                    identity.ST,
                    identity.L,
                    identity.C,
                    identity.serialNumber)
                (not_before, not_after) = openssl.gencrt_identity(
                    identity.issuer.pk,
                    identity.pk)
                identity.not_before = not_before
                identity.not_after = not_after
                identity.status = 'active'
                identity.save()
                messages.success(
                    request,
                    'The certificate for %s '
                    'has been generated successfully' % identity.CN)
        except Exception as e:
            messages.error(
                request, _('The certificate for %s '
                           'cannot be generated: '
                           '%s') % (identity.CN, e))

    return redirect('certs:identity_search')


@login_required
@permission_required('certs.can_pkcs12_identity')
def download_p12(request):
    pk = request.POST['pk']
    password = request.POST['password']
    identity = get_object_or_404(Identity, pk=pk)
    try:
        p12_file = openssl.genp12_identity(identity.issuer.pk,
                                           identity.pk, password, identity.CN)
        resp = HttpResponse(p12_file, content_type='application/x-pkcs12')
        resp['Content-Disposition'] = 'attachment; filename="%s.p12"' % slugify(
            identity.CN)
        return resp
    except Exception as e:
        messages.error(
            request, _('The certificate for %s '
                       'cannot be generated. '
                       'openssl returns an error. (%s)') % (identity.CN, e))
    return redirect('certs:identity_search')


@login_required
@permission_required('certs.can_revoke_identity')
def identity_revoke(request):
    pk = request.POST['pk']
    reason = request.POST['reason']
    identity = get_object_or_404(Identity, pk=pk)
    try:
        openssl.revoke_identity(identity.issuer.pk,
                                identity.pk, reason)
        identity.status = 'revoked'
        identity.revoked_on = datetime.now()
        identity.crl_reason = reason
        identity.save()
        messages.success(
            request,
            'Certificate for %s revoked successfully' % identity.CN)
    except Exception as e:
        messages.error(
            request, _('The certificate for %s '
                       'cannot be revoked. '
                       'openssl returns an error. (%s)') % (identity.CN, e))
    return redirect('certs:identity_search')


@login_required
@permission_required('certs.can_search_server')
def server_search(request):

    srvs = None
    query = request.GET.get('q', '')
    page = request.GET.get('page', 1)

    flt = SQ()

    if not request.user.is_superuser:
        flt &= SQ(issuer_operators=request.user.pk)

    if query:
        flt &= SQ(content=AutoQuery(query))

    srvs = SearchQuerySet().filter(flt).models(Server)

    paginator = Paginator(srvs, 5)

    try:
        srvs_list = paginator.page(page)
    except PageNotAnInteger:
        srvs_list = paginator.page(1)
    except EmptyPage:
        srvs_list = paginator.page(paginator.num_pages)
    return render(
        request,
        'certs/server_search.html',
        {
            'objects_page': srvs_list,
            'query': query,
            'crl_reasons': CRL_REASON_CHOICES
        })


@login_required
@permission_required('certs.add_server')
def server_create(request):
    f = ServerForm(request.user, request.POST or None)

    if f.is_valid():
        issuer = f.cleaned_data['issuer']
        csr = f.cleaned_data['csr']
        issuer = SubCA.objects.get(pk=issuer)
        instance = _from_csr(csr)
        instance.issuer = issuer
        instance.save()
        messages.success(request,
                         _('The certificate request for %s '
                           'has been saved successfully') % instance.CN)
        return redirect('certs:server_search')
    return render(request, 'certs/server_edit.html', {'f': f})


@login_required
@permission_required('certs.change_server')
def server_update(request, pk):
    srv = get_object_or_404(Server, pk=pk)
    f = ServerForm(
        request.user,
        request.POST or None,
        initial={'issuer':srv.issuer.pk, 'csr': srv.csr})

    if f.is_valid():
        issuer = f.cleaned_data['issuer']
        csr = f.cleaned_data['csr']
        issuer = SubCA.objects.get(pk=issuer)
        instance = _from_csr(csr)
        instance.issuer = issuer
        instance.pk = srv.pk
        instance.save()
        messages.success(request,
                         _('The certificate request for %s '
                           'has been saved successfully') % instance.CN)
        return redirect('certs:server_search')
    return render(request, 'certs/server_edit.html', {'f': f})


@login_required
@permission_required('certs.can_generate_server')
def server_generate(request, pk):
    srv = get_object_or_404(Server, pk=pk)
    if srv.status == 'new':

        try:
            (not_before, not_after) = openssl.gencrt_server(
                srv.issuer.pk,
                srv.pk,
                srv.csr)
            srv.not_before = not_before
            srv.not_after = not_after
            srv.status = 'active'
            srv.save()
            messages.success(
                request,
                'Certificate for %s generated successfully' % srv.CN)
        except Exception as e:
            logger.exception('Cannot generate server certificate.')
            messages.error(
                request, _('The certificate for %s '
                           'cannot be generated. '
                           'openssl returns an error. (%s)') % (srv.CN, e))

    return redirect('certs:server_search')

@login_required
@permission_required('certs.delete_server')
def server_delete(request):
    if not 'pk' in request.POST:
        raise Exception('pk not provided!')
    pk = request.POST['pk']
    server = get_object_or_404(Server, pk=int(pk))
    if server.status != 'new':
        messages.error(request,
                         _('The certificate request for %s '
                           'cannot be deleted: invalid status.') % server.CN)
        return redirect('certs:server_search')
    server.delete()
    messages.success(request,
                     _('The certificate request for  %s '
                       'has been deleted successfully') % server.CN)
    return redirect('certs:server_search')

def download_srv_pem(request, pk):
    srv = get_object_or_404(Server, pk=pk)
    try:
        pem_file = openssl.getpem_server(srv.issuer.pk,
                                           srv.pk)
        resp = HttpResponse(pem_file, content_type='application/x-pem-file')
        resp['Content-Disposition'] = 'attachment; filename="%s.pem"' % slugify(
            srv.CN)
        return resp
    except Exception as e:
        messages.error(
            request, _('The certificate for %s '
                       'cannot be generated. '
                       'openssl returns an error. (%s)') % (srv.CN, e))
    return redirect('certs:server_search')


def download_id_pem(request, pk):
    id = get_object_or_404(Identity, pk=pk)
    try:
        pem_file = openssl.getpem_identity(id.issuer.pk,
                                           id.pk)
        resp = HttpResponse(pem_file, content_type='application/x-pem-file')
        resp['Content-Disposition'] = 'attachment; filename="%s.pem"' % slugify(
            id.CN)
        return resp
    except Exception as e:
        messages.error(
            request, _('The certificate for %s '
                       'cannot be generated. '
                       'openssl returns an error. (%s)') % (id.CN, e))
    return redirect('certs:server_search')


@login_required
@permission_required('certs.can_revoke_server')
def server_revoke(request):
    pk = request.POST['pk']
    reason = request.POST['reason']
    srv = get_object_or_404(Server, pk=pk)
    try:
        openssl.revoke_server(srv.issuer.pk,
                                srv.pk, reason)
        srv.status = 'revoked'
        srv.revoked_on = datetime.utcnow()
        srv.crl_reason = reason
        srv.save()
        messages.success(
            request,
            'Certificate for %s revoked successfully' % srv.CN)
    except Exception as e:
        messages.error(
            request, _('The certificate for %s '
                       'cannot be revoked. '
                       'openssl returns an error. (%s)') % (srv.CN, e))
    return redirect('certs:server_search')


def _from_csr(csr):
    req = crypto.load_certificate_request(crypto.FILETYPE_PEM, csr)
    subject = req.get_subject()
    s = Server()
    s.CN = subject.commonName
    s.O = subject.organizationName
    s.OU = subject.organizationalUnitName
    s.ST = subject.stateOrProvinceName
    s.C = subject.countryName
    s.L = subject.localityName
    s.E = subject.emailAddress
    s.csr = csr
    return s
