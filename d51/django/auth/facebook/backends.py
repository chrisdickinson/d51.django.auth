from d51.django.auth.backends import AbstractModelAuthBackend
from d51.django.auth.facebook.models import FacebookID

FACEBOOK_CONNECT_BACKEND_STRING = 'd51.django.auth.facebook.backends.FacebookConnectBackend'

class FacebookConnectBackend(AbstractModelAuthBackend):
    def __init__(self, manager=FacebookID.objects, **kwargs):
        super(FacebookConnectBackend, self).__init__(**kwargs)
        self.manager = manager

    def authenticate(self, **kwargs):
        if not 'request' in kwargs:
            return

        request = kwargs['request']
        try:
            if not request.facebook.check_session(request):
                return
        except ValueError, e:
            # There is a [possible situation][bug] in PyFacebook that causes
            # the "expires" value to be equal to 'None', which causes this
            # exception.  This catches it and returns empty, essentially saying
            # "we're not logged in."
            #
            # [bug]: http://github.com/sciyoshi/pyfacebook/issues/#issue/26
            if str(e) == "invalid literal for int() with base 10: 'None'":
                return
            raise e


        try:
            user = self.manager.get_uid(request.facebook.uid).user
        except self.manager.model.DoesNotExist:
            user = request.user.is_authenticated() and request.user or self._create_new_user(request)
            fb_id = self.manager.create(pk=request.facebook.uid, user=user)
        user.backend = FACEBOOK_CONNECT_BACKEND_STRING
        return user

    def _create_new_user(self, request):
        user_info = request.facebook.users.getInfo([request.facebook.uid], ['name'])[0]
        user_name = user_info['name'].split(' ')
        user = self.user_manager.create(
            username='fb$%s' % request.facebook.uid,
            first_name=user_name[0],
            last_name=user_name[1]
        )
        user.set_unusable_password()
        user.save()
        return user

