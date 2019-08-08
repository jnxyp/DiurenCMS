def inject_profile(request):
    u = request.user
    if u.is_authenticated:
        if hasattr(u, 'profile'):
            return {'profile': u.profile}
    return {}
