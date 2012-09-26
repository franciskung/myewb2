from django.contrib.auth import login as auth_login
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import Context, loader, RequestContext

from emailconfirmation.models import EmailConfirmation
from mailer import send_mail

def confirm_email(request, confirmation_key):
    confirmation_key = confirmation_key.lower()
    email_address = EmailConfirmation.objects.confirm_email(confirmation_key)

    # this only runs if it's a new user confirming their first email address    
    if email_address and email_address.user.email == email_address.email:
        email_address.user.message_set.create(message='Your email address has been confirmed!')

        email_address.user.backend = "django.contrib.auth.backends.ModelBackend"
        auth_login(request, email_address.user)

        c = Context({})
        htmlmessage = loader.get_template("emailconfirmation/welcome.html")
        htmlbody = htmlmessage.render(c)
        txtmessage = loader.get_template("emailconfirmation/welcome.txt")
        txtbody = txtmessage.render(c)

        send_mail(subject='Welcome to myEWB!',
                  txtMessage=txtbody,
                  htmlMessage=htmlbody,
                  fromemail='Francis Kung <franciskung@ewb.ca>',
                  recipients=[email_address.email],
                  use_template=False)

        return HttpResponseRedirect(reverse('home'))
        
    
    return render_to_response("emailconfirmation/confirm_email.html", {
        "email_address": email_address,
    }, context_instance=RequestContext(request))
