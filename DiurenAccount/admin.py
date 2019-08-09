from django.contrib import admin

# Register your models here.
from DiurenAccount.models import UserProfile
from django.utils.html import format_html


class UserProfileAdmin(admin.ModelAdmin):
    def avatar_image(self, obj: UserProfile):
        return format_html(
            '<img style="max-width:3em" src="{url}"/>'.format(url=obj.avatar_urls.SMALL))

    list_display = ('__str__', 'avatar_image', 'nick', 'language')
    list_display_links = ('avatar_image', '__str__',)
    list_editable = ('nick',)


admin.site.register(UserProfile, UserProfileAdmin)
