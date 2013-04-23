from django.contrib import admin
from django.template.loader import render_to_string

from gatekeeper.models import ModeratedObject


class ModeratedObjectAdmin(admin.ModelAdmin):
    list_display = ('object_name', 'timestamp', 'moderation_status', 'flagged', 'long_desc')
    list_editable = ('moderation_status', 'flagged')
    list_filter = ['moderation_status', 'flagged']

    def long_desc(self, obj):
        return "%s" % render_to_string('moderation/long_desc.html', {'obj': obj.content_object})
    long_desc.short_description = 'Object Description'
    long_desc.allow_tags = True

    def object_name(self, obj):
        return "%s" % obj

admin.site.register(ModeratedObject, ModeratedObjectAdmin)
