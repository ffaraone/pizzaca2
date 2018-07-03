import os
import subprocess
from datetime import datetime
from distutils.spawn import find_executable
from urllib.parse import urljoin

from OpenSSL import crypto

from django.conf import settings
from django.template.loader import render_to_string


OPENSSL = find_executable('openssl')


PEM_X509_HEADER = '-----BEGIN CERTIFICATE-----\n'
PEM_X509_FOOTER = '\n-----END CERTIFICATE-----'

PEM_CSR_HEADER = '-----BEGIN CERTIFICATE REQUEST-----\n'
PEM_CSR_FOOTER = '\n-----END CERTIFICATE REQUEST-----'

BOUNDARIES = {
    'x509': (PEM_X509_HEADER, PEM_X509_FOOTER),
    'csr': (PEM_CSR_HEADER, PEM_CSR_FOOTER)
}


def render_to_file(template, filename, context):
    with open(filename, 'w') as f:
        f.write(render_to_string(template, context))


def touch(path):
    with open(path, 'a'):
        os.utime(path, None)


def strip_pem_boundaries(pem, obj_type='x509'):
    """remove PEM boundaries from certificate"""
    header = BOUNDARIES[obj_type][0]
    footer = BOUNDARIES[obj_type][1]
    pem = '\n'.join(pem.strip(os.linesep).splitlines())
    if pem.startswith(header) \
            and pem.endswith(footer):
        pem = pem[len(header): -len(footer)]
    return pem


def _parse_asn1_gentime(datestring):
    datestring = datestring.decode()
    if 'Z' in datestring:
        datetime_part = datestring[0:14]
        return datetime.strptime(datetime_part, '%Y%m%d%H%M%S')


def _mkserial(path):
    with open(path, 'w') as f:
        f.write('01')


def _run(params):
    p = subprocess.Popen(
        params, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (out, err) = p.communicate()

    if p.returncode != 0:
        raise Exception(err)


def gencrl_stdsub(pk, kind):
    base_dir = os.path.join(settings.CA_ROOT, 'stdsub', str(pk))
    ca_conf = os.path.join(base_dir, 'etc', '%s-ca.conf' % kind)
    params = [
        OPENSSL,
        'ca',
        '-gencrl',
        '-config', ca_conf,
        '-out', os.path.join(base_dir, 'ca', 'crl', 'pem-sub-ca.crl'),
    ]
    _run(params)
    params = [
        OPENSSL,
        'crl',
        '-in', os.path.join(base_dir, 'ca', 'crl', 'pem-sub-ca.crl'),
        '-out', os.path.join(base_dir, 'ca', 'crl', 'sub-ca.crl'),
        '-outform', 'der'
    ]
    _run(params)


def gencrl_root(pk):
    base_dir = os.path.join(settings.CA_ROOT, 'stdroot', str(pk))
    ca_conf = os.path.join(base_dir, 'etc', 'root-ca.conf')
    params = [
        OPENSSL,
        'ca',
        '-gencrl',
        '-config', ca_conf,
        '-out', os.path.join(base_dir, 'ca', 'crl', 'pem-root-ca.crl'),
    ]
    _run(params)
    params = [
        OPENSSL,
        'crl',
        '-in', os.path.join(base_dir, 'ca', 'crl', 'pem-root-ca.crl'),
        '-out', os.path.join(base_dir, 'ca', 'crl', 'root-ca.crl'),
        '-outform', 'der'
    ]
    _run(params)


def create_stdsub(pk, kind, rootpk, CN, O, OU, C):
    root_ca_conf = os.path.join(settings.CA_ROOT,
                                'stdroot',
                                str(rootpk),
                                'etc',
                                'root-ca.conf')

    base_dir = os.path.join(settings.CA_ROOT, 'stdsub', str(pk))
    base_url = urljoin(settings.BASE_URL,
                       'ca/subca/resource/%s' % str(pk))

    os.makedirs(os.path.join(base_dir, 'etc'))
    os.makedirs(os.path.join(base_dir, 'ca', '%s-ca' % kind, 'private'))
    os.makedirs(os.path.join(base_dir, 'ca', '%s-ca' % kind, 'db'))
    os.makedirs(os.path.join(base_dir, 'ca', 'crl'))
    os.makedirs(os.path.join(base_dir, 'ca', 'certs'))
    os.chmod(os.path.join(base_dir, 'ca', '%s-ca' % kind, 'private'), 0o700)
    touch(
        os.path.join(base_dir, 'ca', '%s-ca' % kind, 'db', '%s-ca.db' % kind))
    touch(
        os.path.join(base_dir, 'ca', '%s-ca' % kind, 'db',
                     '%s-ca.db.attr' % kind))
    _mkserial(
        os.path.join(base_dir, 'ca', '%s-ca' % kind, 'db',
                     '%s-ca.crt.srl' % kind))
    _mkserial(
        os.path.join(base_dir, 'ca', '%s-ca' % kind, 'db',
                     '%s-ca.crl.srl' % kind))

    ca_conf = os.path.join(base_dir, 'etc', '%s-ca.conf' % kind)
    render_to_file(
        'openssl/%s-ca.conf' % kind,
        ca_conf,
        {
            'base_dir': base_dir,
            'base_url': base_url,
            'CN': CN,
            'O': O,
            'OU': OU,
            'C': C
        }
    )

    params = [
        OPENSSL,
        'req',
        '-new',
        '-config', ca_conf,
        '-out', os.path.join(base_dir, 'ca', '%s-ca.csr' % kind),
        '-keyout', os.path.join(
            base_dir, 'ca', '%s-ca' % kind, 'private', '%s-ca.key' % kind)
    ]
    _run(params)

    params = [
        OPENSSL,
        'ca',
        '-config', root_ca_conf,
        '-in', os.path.join(base_dir, 'ca', '%s-ca.csr' % kind),
        '-out', os.path.join(base_dir, 'ca', 'sub-ca.crt'),
        '-extensions', 'signing_ca_ext',
        '-batch'
    ]
    _run(params)

    if kind == 'identity':
        req_conf = os.path.join(base_dir, 'etc', '%s.conf' % kind)
        render_to_file(
            'openssl/%s.conf' % kind,
            req_conf, dict()
        )
    gencrl_stdsub(pk, kind)
    with open(os.path.join(base_dir, 'ca', 'sub-ca.crt'), 'rb') as f:
        pem_data = f.read()
    x509 = crypto.load_certificate(crypto.FILETYPE_PEM, pem_data)
    not_before = _parse_asn1_gentime(x509.get_notBefore())
    not_after = _parse_asn1_gentime(x509.get_notAfter())
    return (not_before, not_after)


def get_sub_crt(pk):
    base_dir = os.path.join(settings.CA_ROOT, 'stdsub', str(pk))
    with open(os.path.join(base_dir, 'ca', 'sub-ca.crt'), 'r') as f:
        return f.read()


def create_stdroot(pk, CN, O, OU, C):
    base_dir = os.path.join(settings.CA_ROOT, 'stdroot', str(pk))
    base_url = urljoin(settings.BASE_URL,
                       'ca/ca/resource/%s' % str(pk))

    os.makedirs(os.path.join(base_dir, 'etc'))
    os.makedirs(os.path.join(base_dir, 'ca', 'root-ca', 'private'))
    os.makedirs(os.path.join(base_dir, 'ca', 'root-ca', 'db'))
    os.makedirs(os.path.join(base_dir, 'ca', 'crl'))
    os.makedirs(os.path.join(base_dir, 'ca', 'certs'))
    os.chmod(os.path.join(base_dir, 'ca', 'root-ca', 'private'), 0o700)
    touch(os.path.join(base_dir, 'ca', 'root-ca', 'db', 'root-ca.db'))
    touch(os.path.join(base_dir, 'ca', 'root-ca', 'db', 'root-ca.db.attr'))
    _mkserial(os.path.join(base_dir, 'ca', 'root-ca', 'db', 'root-ca.crt.srl'))
    _mkserial(os.path.join(base_dir, 'ca', 'root-ca', 'db', 'root-ca.crl.srl'))

    root_ca_conf = os.path.join(base_dir, 'etc', 'root-ca.conf')
    render_to_file(
        'openssl/root-ca.conf',
        root_ca_conf,
        {
            'base_dir': base_dir,
            'base_url': base_url,
            'CN': CN,
            'O': O,
            'OU': OU,
            'C': C
        }
    )

    params = [
        OPENSSL,
        'req',
        '-new',
        '-config', root_ca_conf,
        '-out', os.path.join(base_dir, 'ca', 'root-ca.csr'),
        '-keyout', os.path.join(
            base_dir, 'ca', 'root-ca', 'private', 'root-ca.key')
    ]
    _run(params)

    params = [
        OPENSSL,
        'ca',
        '-selfsign',
        '-config', root_ca_conf,
        '-in', os.path.join(base_dir, 'ca', 'root-ca.csr'),
        '-out', os.path.join(base_dir, 'ca', 'root-ca.crt'),
        '-extensions', 'root_ca_ext',
        '-batch'
    ]
    _run(params)
    gencrl_root(pk)
    # params = [
    #     OPENSSL,
    #     'ca',
    #     '-gencrl',
    #     '-config', root_ca_conf,
    #     '-out', os.path.join(base_dir, 'ca', 'crl', 'root-ca.crl')    ]
    # _run(params)
    with open(os.path.join(base_dir, 'ca', 'root-ca.crt'), 'rb') as f:
        pem_data = f.read()
    x509 = crypto.load_certificate(crypto.FILETYPE_PEM, pem_data)
    not_before = _parse_asn1_gentime(x509.get_notBefore())
    not_after = _parse_asn1_gentime(x509.get_notAfter())
    return (not_before, not_after)


def get_root_crt(pk):
    base_dir = os.path.join(settings.CA_ROOT, 'stdroot', str(pk))
    with open(os.path.join(base_dir, 'ca', 'root-ca.crt'), 'r') as f:
        return f.read()


def gencsr_identity(ca_pk, identity_pk, CN, T, GN, SN,
                    E, O, OU, ST, L, C, serialNumber, related_company=''):

    base_dir = os.path.join(settings.CA_ROOT, 'stdsub', str(ca_pk))
    identity_conf = os.path.join(base_dir, 'etc', 'identity.conf')
    subject = '/CN=%s/GN=%s/SN=%s/O=%s/C=%s' % \
        (CN, GN, SN, O, C)

    if ST:
        subject += '/ST=%s' % ST
    if OU:
        subject += '/OU=%s' % OU
    if L:
        subject += '/localityName=%s' % L
    if T:
        subject += '/title=%s' % T
    if related_company:
        subject += '/2.5.4.97=%s' % related_company

    subject += '/serialNumber=%s/emailAddress=%s' % (serialNumber, E)


    params = [
        OPENSSL,
        'req',
        '-new',
        '-config', identity_conf,
        '-out', os.path.join(
            base_dir, 'ca', 'certs', '%s.csr' % str(identity_pk)),
        '-keyout', os.path.join(
            base_dir, 'ca', 'identity-ca',
            'private', '%s.key' % str(identity_pk)),
        '-subj', subject,
        '-nodes'
    ]
    _run(params)


    params = [
        OPENSSL,
        'req',
        '-new',
        '-config', identity_conf,
        '-out', os.path.join(
            base_dir, 'ca', 'certs', '%s.csr' % str(identity_pk)),
        '-keyout', os.path.join(
            base_dir, 'ca', 'identity-ca',
            'private', '%s.key' % str(identity_pk)),
        '-subj', subject,
        '-nodes'
    ]
    _run(params)


def gencrt_identity(ca_pk, identity_pk, subject=None):
    base_dir = os.path.join(settings.CA_ROOT, 'stdsub', str(ca_pk))
    identity_conf = os.path.join(base_dir, 'etc', 'identity-ca.conf')
    csr_file = os.path.join(
        base_dir, 'ca', 'certs', '%s.csr' % str(identity_pk))
    crt_file = os.path.join(
        base_dir, 'ca', 'certs', '%s.pem' % str(identity_pk))
    params = [
        OPENSSL,
        'ca',
        '-config', identity_conf,
        '-in', csr_file,
        '-out', crt_file,
        '-extensions',
        'identity_ext',
        '-batch'
    ]
    if subject:
        params.append('-subj')
        params.append(subject)

    print(params)
    _run(params)
    with open(crt_file, 'rb') as f:
        pem_data = f.read()
    x509 = crypto.load_certificate(crypto.FILETYPE_PEM, pem_data)
    not_before = _parse_asn1_gentime(x509.get_notBefore())
    not_after = _parse_asn1_gentime(x509.get_notAfter())
    return (not_before, not_after)


def gencrt_server(ca_pk, server_pk, csr):
    base_dir = os.path.join(settings.CA_ROOT, 'stdsub', str(ca_pk))
    component_conf = os.path.join(base_dir, 'etc', 'component-ca.conf')
    csr_file = os.path.join(
        base_dir, 'ca', 'certs', '%s.csr' % str(server_pk))

    with open(csr_file, 'w') as f:
        f.write(csr)

    crt_file = os.path.join(
        base_dir, 'ca', 'certs', '%s.pem' % str(server_pk))
    params = [
        OPENSSL,
        'ca',
        '-config', component_conf,
        '-in', csr_file,
        '-out', crt_file,
        '-extensions',
        'server_ext',
        '-batch'
    ]
    _run(params)
    with open(crt_file, 'rb') as f:
        pem_data = f.read()
    x509 = crypto.load_certificate(crypto.FILETYPE_PEM, pem_data)
    not_before = _parse_asn1_gentime(x509.get_notBefore())
    not_after = _parse_asn1_gentime(x509.get_notAfter())
    return (not_before, not_after)


def getpem_server(ca_pk, server_pk):
    base_dir = os.path.join(settings.CA_ROOT, 'stdsub', str(ca_pk))
    crt_file = os.path.join(
        base_dir, 'ca', 'certs', '%s.pem' % str(server_pk))
    with open(crt_file, 'rb') as f:
        return f.read()


def getpem_identity(ca_pk, id_pk):
    base_dir = os.path.join(settings.CA_ROOT, 'stdsub', str(ca_pk))
    crt_file = os.path.join(
        base_dir, 'ca', 'certs', '%s.pem' % str(id_pk))
    with open(crt_file, 'rb') as f:
        return f.read()


def genp12_identity(ca_pk, identity_pk, passwd, alias):
    base_dir = os.path.join(settings.CA_ROOT, 'stdsub', str(ca_pk))
    key_file = os.path.join(
        base_dir, 'ca', 'identity-ca',
        'private', '%s.key' % str(identity_pk))
    crt_file = os.path.join(
        base_dir, 'ca', 'certs', '%s.pem' % str(identity_pk))
    out_file = os.path.join(
        base_dir, 'ca', 'certs', '%s.p12' % str(identity_pk))

    params = [
        OPENSSL,
        'pkcs12',
        '-export',
        '-name', alias,
        '-inkey', key_file,
        '-in', crt_file,
        '-out', out_file,
        '-password',
        'pass:%s' % passwd
    ]
    _run(params)
    with open(out_file, 'rb') as f:
        return f.read()


def revoke_identity(ca_pk, identity_pk, reason):
    base_dir = os.path.join(settings.CA_ROOT, 'stdsub', str(ca_pk))
    crt_file = os.path.join(
        base_dir, 'ca', 'certs', '%s.pem' % str(identity_pk))
    identity_conf = os.path.join(base_dir, 'etc', 'identity-ca.conf')
    params = [
        OPENSSL,
        'ca',
        '-config', identity_conf,
        '-revoke', crt_file,
        '-crl_reason', reason
    ]
    _run(params)
    gencrl_stdsub(ca_pk, 'identity')

def revoke_server(ca_pk, srv_pk, reason):
    base_dir = os.path.join(settings.CA_ROOT, 'stdsub', str(ca_pk))
    crt_file = os.path.join(
        base_dir, 'ca', 'certs', '%s.pem' % str(srv_pk))
    component_conf = os.path.join(base_dir, 'etc', 'component-ca.conf')
    params = [
        OPENSSL,
        'ca',
        '-config', component_conf,
        '-revoke', crt_file,
        '-crl_reason', reason
    ]
    _run(params)
    gencrl_stdsub(ca_pk, 'component')
