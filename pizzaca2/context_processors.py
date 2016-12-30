from hashlib import md5


def gravatar_hash(request):
    if hasattr(request.user, 'email'):
        m = md5()
        m.update(request.user.email.encode('utf-8'))
        return {'gravatar_hash': m.hexdigest()}
    return dict()
