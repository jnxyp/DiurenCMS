def inject_cloud_user(request):
    u = request.user
    if u.is_authenticated:
        if hasattr(u, 'cloud_user'):
            return {'cloud_user': u.cloud_user}
        else:
            return {'cloud_user': False}