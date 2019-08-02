from DiurenCMS import settings


# 为所有模板添加SETTINGS变量
def inject_settings(request):
    return {'SETTINGS': settings}


# 将每个APP的APP CONFIG写入模板
def inject_app_configs(request):
    app_configs = dict()
    for config_name in settings.INSTALLED_APPS:
        if config_name.endswith('Config'):
            mod_name = '.'.join(config_name.split('.')[:-1])
            config_name = config_name.split('.')[-1]

            config = __import__(mod_name, fromlist=[config_name])

            app_configs[config_name.replace('Config', '').upper()] = config
    return app_configs


if __name__ == '__main__':
    print(inject_app_configs(None))
