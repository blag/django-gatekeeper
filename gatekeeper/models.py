from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import ugettext_lazy as _
import datetime
import gatekeeper

STATUS_CHOICES = (
    (1, _("Approved")),
    (0, _("Pending")),
    (-1, _("Rejected")),
)

STATUS_ON_FLAG = getattr(settings, "GATEKEEPER_STATUS_ON_FLAG", None)

class ModeratedObjectManager(models.Manager):

    def get_for_instance(self, obj):
        ct = ContentType.objects.get_for_model(obj.__class__)
        try:
            mo = ModeratedObject.objects.get(content_type=ct, object_id=obj.pk)
            return mo
        except ModeratedObject.DoesNotExist:
            pass

class ModeratedObject(models.Model):

    objects = ModeratedObjectManager()

    timestamp = models.DateTimeField(auto_now_add=True, blank=True, null=True, \
                                     verbose_name="created date")

    moderation_status = models.IntegerField(choices=STATUS_CHOICES,
                                verbose_name=_('moderation status'))
    moderation_status_by = models.ForeignKey(User, blank=True, null=True,
                                verbose_name=_('moderation status by'))
    moderation_status_date = models.DateTimeField(blank=True, null=True,
                                verbose_name=_('moderation status date'))
    moderation_reason = models.CharField(max_length=100, blank=True,
                                verbose_name=_('moderation reason'))

    flagged = models.BooleanField(default=False, verbose_name=_('flagged'))
    flagged_by = models.ForeignKey(User, blank=True, null=True,
                                   related_name='flagged objects',
                                   verbose_name=_('flagged by'))
    flagged_date = models.DateTimeField(blank=True, null=True,
                                        verbose_name=_('flagged date'))

    content_type = models.ForeignKey(ContentType,
                                     verbose_name=_('content type'))
    object_id = models.PositiveIntegerField(verbose_name=_('object id'))
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    created_ip = models.IPAddressField(_('Created user IP'), blank=True, null=True)
    created_by = models.ForeignKey(User, blank=True, null=True, \
                                   related_name="created_moderated_objects",
                                   verbose_name=_('created by'))

    class Meta:
        ordering = ['timestamp']

    def __unicode__(self):
        return "[%s] %s" % (self.get_moderation_status_display(),
                            self.content_object)

    def get_absolute_url(self):
        if hasattr(self.content_object, "get_absolute_url"):
            return self.content_object.get_absolute_url()

    def _moderate(self, status, user, reason=None):
        self.moderation_status = status
        self.moderation_status_by = user
        self.moderation_status_date = datetime.datetime.now()
        self.moderation_reason = reason
        self.save()
        gatekeeper.post_moderation.send(sender=ModeratedObject, instance=self)

    def flag(self, user):
        self.flagged = True
        self.flagged_by = user
        self.flagged_date = datetime.datetime.now()
        if STATUS_ON_FLAG:
            self.moderation_status = STATUS_ON_FLAG
            self.moderation_status_by = user
            self.moderation_status_date = self.flagged_date
            gatekeeper.post_moderation.send(sender=ModeratedObject, instance=self)
        self.save()
        gatekeeper.post_flag.send(sender=ModeratedObject, instance=self)

    def approve(self, user, reason=''):
        self._moderate(1, user, reason)

    def reject(self, user, reason=''):
        self._moderate(-1, user, reason)

    @models.permalink
    def object_change_admin_url(self):
        return ('admin:%s_%s_change' % (self.content_type.app_label,
                                        self.content_type.model),
                [self.object_id, ])

    def object_change_admin_link(self):
        try:
            return u'<a href="%s">%s</a>' % \
                        (self.object_change_admin_url(), _('View'))
        except:
            return self.get_absolute_url()
    object_change_admin_link.allow_tags = True
    object_change_admin_link.short_description = _('link')


class ModerationMixin(object):
    """
    Chek object moderation status
    """
    def is_approved(self):
        return self.moderation_status == gatekeeper.APPROVED_STATUS

    def is_rejected(self):
        return self.moderation_status == gatekeeper.REJECTED_STATUS

    def is_pending(self):
        return self.moderation_status == gatekeeper.PENDING_STATUS
