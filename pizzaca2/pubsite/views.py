from io import BytesIO
from zipfile import ZipFile

from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.template.defaultfilters import slugify
from haystack.inputs import AutoQuery, Clean, Exact
from haystack.query import SearchQuerySet, SQ

#from calzone.models import Identity, Server
from ..engine import openssl
from ..ca.models import CA


def cas(request):
    page = request.GET.get('page', 1)
    cas = CA.objects.filter(status = 'active').order_by('-last_modified')
    paginator = Paginator(cas, 5)
    try:
        cas = paginator.page(page)
    except PageNotAnInteger:
        cas = paginator.page(1)
    except EmptyPage:
        cas = paginator.page(paginator.num_pages)
    return render(request, 'pubsite/cas.html', {'objects_page': cas})


def servers(request, page=1):
    srvs = None
    query = request.GET.get('q', '')
    page = request.GET.get('page', 1)
    flt = SQ()

    if query:
        flt &= SQ(content=AutoQuery(query))


    srvs = SearchQuerySet().filter(flt).exclude(status='new').models(Server)

    paginator = Paginator(srvs, 5)


    try:
        srvs_list = paginator.page(page)
    except PageNotAnInteger:
        srvs_list = paginator.page(1)
    except EmptyPage:
        srvs_list = paginator.page(paginator.num_pages)
    return render(
        request,
        'pubsite/servers.html',
        {
            'objects_page': srvs_list,
            'query': query
        }
    )


def identities(request):
    ids = None
    query = request.GET.get('q', '')
    page = request.GET.get('page', 1)
    flt = SQ()

    if query:
        flt &= SQ(content=AutoQuery(query))


    ids = SearchQuerySet().filter(flt).exclude(status='new').models(Identity)

    paginator = Paginator(ids, 5)


    try:
        ids_list = paginator.page(page)
    except PageNotAnInteger:
        ids_list = paginator.page(1)
    except EmptyPage:
        ids_list = paginator.page(paginator.num_pages)
    return render(
        request,
        'pubsite/identities.html',
        {
            'objects_page': ids_list,
            'query': query
        }
    )

def bundle(request, pk):
    stream = BytesIO()
    bundle = []
    with ZipFile(stream, mode='w') as f:
        ca = get_object_or_404(CA, pk=pk)
        for sub in ca.sub_cas.all():
            sub_crt = openssl.get_sub_crt(sub.pk)
            bundle.append(sub_crt)
            file_name = 's_%s_%s.crt' % (str(sub.pk), slugify(sub.CN))
            f.writestr(file_name, sub_crt)
        file_name = 'r_%s_%s.crt' % (str(ca.pk), slugify(ca.CN))
        ca_crt = openssl.get_root_crt(ca.pk)
        bundle.append(ca_crt)
        f.writestr(file_name, ca_crt)
        f.writestr('ca-bundle.crt', ''.join(bundle))
    resp = HttpResponse(stream.getvalue(), content_type='application/zip')
    resp['Content-Disposition'] = 'attachment; filename="ca-bundle.zip"'
    stream.close()
    return resp
