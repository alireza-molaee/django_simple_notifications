from django.db import models
from django.db.models import Q
from django.apps import apps as django_apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def get_user_model():
    """
    Returns the User model that is active in this project.
    """
    try:
        return django_apps.get_model(settings.AUTH_USER_MODEL)
    except ValueError:
        raise ImproperlyConfigured("AUTH_USER_MODEL must be of the form 'app_label.model_name'")
    except LookupError:
        raise ImproperlyConfigured(
            "AUTH_USER_MODEL refers to model '%s' that has not been installed" % settings.AUTH_USER_MODEL
        )


class NotSeenQuerySet(models.QuerySet):
    """
    this is shortcut to filter notifications that not seen yet
    """
    def not_seen(self, user):
        return self.filter(Q(seen_date__isnull=True) & Q(user=user))


class Notification(models.Model):
    user = models.ForeignKey(get_user_model(), related_name="notifications",
                             related_query_name="user")
    icon = models.CharField(max_length=40)
    COLOR_WARNING = '#f39c12'
    COLOR_DANGER = '#f56954'
    COLOR_INFO = '#00c0ef'
    COLOR_SUCCESS = '#00a65a'
    COLOR_PRIMARY = '#3c8dbc'
    COLOR_GRAY = '#d2d6de'
    COLOR_BLACK = '#111111'
    COLOR_CHOICES = (
        (COLOR_DANGER, 'Danger'),
        (COLOR_WARNING, 'Warning'),
        (COLOR_SUCCESS, 'Success'),
        (COLOR_INFO, 'Info'),
        (COLOR_PRIMARY, 'Primary'),
        (COLOR_GRAY, 'Gray'),
        (COLOR_BLACK, 'Black'),
    
    )
    color = models.CharField(max_length=7, choices=COLOR_CHOICES,
                             default=COLOR_BLACK)
    content = models.TextField(max_length=200)
    url = models.URLField(blank=True, null=True)
    seen_date = models.DateField(blank=True, null=True, editable=False)
    send_date = models.DateField(auto_now_add=True)

    objects = NotSeenQuerySet.as_manager()
    
    @property
    def seen(self):
        """
        for checking seen status
        :return: True or False
        """
        if self.seen_date is None:
            return False
        else:
            return True

    @classmethod
    def send(cls, users, content, icon, color, url=None, commit=True):
        """
        use this for send notification
        :param users: list of user we want to send them notification
        :type users: list
        :param content: content of notification
        :param icon: name of icon class
        :param color: color number (hex)
        :param url: url for target of notification (optional)
        :param commit: for commit to save (default: True)(optional)
        :type commit: bool
        :return: instances of Notification class (list)
        """
        result = []
        for user in users:
            notification = cls(user=user, content=content, icon=icon,
                               color=color, url=url)
            notification.full_clean()
            if commit:
                notification.save()
            result.append(notification)
        return result

    @classmethod
    def seen_all(cls, user):
        import datetime
        cls.objects.not_seen(user).update(seen_date=datetime.date.today())

    @classmethod
    def del_all(cls):
        from datetime import date, timedelta
        cls.objects.filter(seen_date__lte=date.today()-timedelta(1)).delete()
        
    def get_icon_html(self):
        out_html = '<i class="{} {}" style="color:{};"></i>'.format(
            self.icon.split('-')[0], self.icon, self.color)
        return out_html #TODO: add fontawsome to admin list template
    
    def get_link(self):
        out_html = '<a href="{}"><i class="fa fa-link"></i>Link</a>'.format(
            self.url)
        return out_html

    class Meta:
        ordering = ['-id']
