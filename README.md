SSO PoC
=======

POCs to test SSO based interaction with web and services.

Refer (https://docs.google.com/a/plivo.com/drawings/d/1adtR_GOU-Wo1CDlzER3OjtsBLn_cMhDGT6BcgZZM_dA/edit?usp=sharing)[this diagram]

Contains three parts:
* django-idp: Identity provider with Django and OAuth toolkit
* plivo-web-flask: Flask web app serving minimal login/dashboard pages
* plivo-service-flask: Flask service to simulate a long running service op
