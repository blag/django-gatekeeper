from django.contrib import admin
from gatekeeper.models import ModeratedObject
from django.utils.translation import ugettext_lazy as _


class ModeratedObjectAdmin(admin.ModelAdmin):
    list_display = ('object_name', 'timestamp', 'created_by', 'created_ip', \
                    'moderation_status', 'moderation_status_by', \
                    'flagged', 'object_change_admin_link')
    list_editable = ('moderation_status', 'flagged')
    list_filter = ['moderation_status', 'flagged', 'content_type', ]
    ordering = ['-timestamp', ]
    raw_id_fields = ['created_by', 'flagged_by', 'moderation_status_by']
    #readonly_fields = ['created_by', 'created_ip', 'timestamp']
    radio_fields = {'moderation_status': admin.HORIZONTAL}
    fieldsets = (
        (_('Moderation'), {
            'fields': ['moderation_status', 'moderation_status_by', 'moderation_status_date', 'moderation_reason'],
        }),
        (_('Flagged'), {
            'fields': ['flagged', 'flagged_by', 'flagged_date'],
        }),
        (_('Meta'), {
            'fields': [ ('content_type', 'object_id'), ('created_ip', 'created_by',)],
        })
    )


    def object_name(self, obj):
        return "%s" % obj

admin.site.register(ModeratedObject, ModeratedObjectAdmin)
