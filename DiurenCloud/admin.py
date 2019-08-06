from django.contrib import admin

# Register your models here.
from DiurenCloud.models import CloudUser, CloudDirectory, CloudFile


@admin.register(CloudUser)
class CloudUserAdmin(admin.ModelAdmin):
    pass


@admin.register(CloudDirectory)
class CloudDirectoryAdmin(admin.ModelAdmin):
    pass


@admin.register(CloudFile)
class CloudFileAdmin(admin.ModelAdmin):
    pass
