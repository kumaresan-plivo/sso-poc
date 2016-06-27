SSO PoC
=======

POCs to test SSO based interaction with web and services.

Refer [this diagram](https://docs.google.com/a/plivo.com/drawings/d/1adtR_GOU-Wo1CDlzER3OjtsBLn_cMhDGT6BcgZZM_dA/edit?usp=sharing)

Contains three parts:
* **idp**: Identity provider in Django and OAuth toolkit
* **plivo-web**: Flask web app serving minimal login/dashboard pages
* **plivo-service**: Flask service to simulate a long running service op
* Also uses local redis instance for cache

Pros and Cons
-------------

| Topic | Stormpath | Django SSO |
| ----- | -------- | ---------- |
| Authentication support | Works | Works, except no JWT by default |
| Authorization support | Only by extending customData and creating directories/groups. This means atleast one extra API call at login to search the user and custom data | No support OOTB. Needs trivial changes to add user level scopes, more changes to add application level scopes. But no extra API call needed for returning scopes |
| Registration | Provides registration APIs including email/password recovery | Need to add registration/related APIs(or just use registration package to host the entire flow) |


Other take-aways
----------------

* In both approaches, it's up to the app to check if the given user/token has access to required functionality.
* Need to write decorators/common-utils for permission checks, cache token validation and RT flow in either case.
* Django OAuth toolkit doesn't issue JWT. So the tokens we send to front-end must have restricted scopes and should always be validated
* There are probably some caching gotchas involved in either case. Like actual tokens expiring before cache expires. Also need to decide if we have to use user Id as key or something else. This demo uses AT as key which is not ideal if AT length is too big for Redis.


Changes in oauth-provider
-------------------------

Changes made to OAuth toolkit to support user level scopes:

* oauth_validators.py

```python
    def validate_scopes(self, client_id, scopes, client, request, *args, **kwargs):
        """
        Ensure required scopes are permitted (as specified in the settings file)
        """
        extra_scopes = [p.name for p in request.user.user_permissions.all()]
        total_scopes = extra_scopes + oauth2_settings._SCOPES
        return set(scopes).issubset(set(total_scopes))

    def get_default_scopes(self, client_id, request, *args, **kwargs):
        extra_scopes = [p.name for p in request.user.user_permissions.all()]
        print(extra_scopes)
        return extra_scopes + oauth2_settings._DEFAULT_SCOPES
```

* Create a permission and add this permission to the user from admin

```python
import django; django.setup()
from django.contrib.auth.models import Permission

p = Permission()
p.name = 'ComplexScope'
p.content_type_id = 7
p.save()

```
