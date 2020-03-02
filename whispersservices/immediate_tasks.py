from celery import shared_task, current_task
import re
from datetime import datetime
from rest_framework.settings import api_settings
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from whispersservices.models import *


def jsonify_errors(data):
    if isinstance(data, list) or isinstance(data, str):
        # Errors raised as a list are non-field errors.
        if hasattr(settings, 'NON_FIELD_ERRORS_KEY'):
            key = settings.NON_FIELD_ERRORS_KEY
        else:
            key = api_settings.NON_FIELD_ERRORS_KEY
        return {key: data}
    else:
        return data


def construct_notification_email(recipient_email, subject, html_body, include_boilerplate=True):
    # subject = "An action by " + source + " requires your attention" if not subject else subject
    # if client_page == 'event':
    #     event_id_string = str(event)
    #     url = settings.APP_WHISPERS_URL + 'event/' + event_id_string + '/'
    # elif client_page == 'userdashboard':
    #     url = settings.APP_WHISPERS_URL + 'userdashboard' + '/'
    # else:
    #     url = settings.APP_WHISPERS_URL
    # html_body = body + "<a href='" + url + ">" + url + "</a>"

    # append the boilerplate text to the end of the email body
    if include_boilerplate:
        boilerplate = Configuration.objects.filter(name='email_boilerplate').first()
        if boilerplate:
            html_body += boilerplate.value

    # create a plain text body by remove HTML tags from the html_body
    body = html_body
    body = body.replace('<h1>', '').replace('</h1>', '\r\n').replace('<h2>', '').replace('</h2>', '\r\n')
    body = body.replace('<h3>', '').replace('</h3>', '\r\n').replace('<h4>', '').replace('</h4>', '\r\n')
    body = body.replace('<h5>', '').replace('</h5>', '\r\n').replace('<p>', '').replace('</p>', '\r\n')
    body = body.replace('<span>', '').replace('</span>', ' ').replace('<strong>', '').replace('</strong>', '')
    body = body.replace('<br>', '\r\n').replace('&nbsp;', ' ').replace('<table>', '').replace('</table>', '\r\n')
    body = body.replace('<thead>', '').replace('</thead>', '\r\n').replace('<tbody>', '').replace('</tbody>', '\r\n')
    body = body.replace('<tr>', '').replace('</tr>', '\r\n').replace('<td>', '').replace('</td>', ' ')
    body = body.replace('</a>', '')
    re.sub(r'<a\s.*>', '', body)
    # body += url
    from_address = settings.EMAIL_WHISPERS
    to_list = [recipient_email, ]
    bcc_list = []
    reply_list = [settings.EMAIL_WHISPERS, ]
    headers = None  # {'Message-ID': 'foo'}
    email = EmailMultiAlternatives(subject, body, from_address, to_list, bcc_list, reply_to=reply_list, headers=headers)
    email.attach_alternative(html_body, "text/html")
    if settings.ENVIRONMENT in ['production', 'test']:
        try:
            email.send(fail_silently=False)
        except TypeError:
            message = "Notification saved but send email failed, please contact the administrator."
            # raise serializers.ValidationError(jsonify_errors(message))
            print(jsonify_errors(message))
    return email


@shared_task(name='generate_notification_task')
def generate_notification(recipients, source, event_id, client_page, subject, body,
                          send_email=False, email_to=None):
    if not recipients or not subject:
        # notify admins of error
        email_address_whispers = Configuration.objects.filter(name='email_address_whispers').first()
        if email_address_whispers and email_address_whispers.value.count('@') == 1:
            new_recip = email_address_whispers.value
        else:
            new_recip = settings.EMAIL_WHISPERS
        new_subject = "WHISPERS ADMIN: Problem Encountered During generate_notification_task"
        new_body = "While generating a notification, a problem was encountered. No notification was created."
        new_body += " The cause of the problem was"
        if not recipients and not subject:
            new_body += " a null recipient list and a null subject."
        elif not recipients:
            new_body += " a null recipient list."
        elif not subject:
            new_body += " a null subject."
        new_body += " Problem encountered at " + datetime.now().strftime("%m/%d/%Y %H:%M:%S")
        new_body += " during task " + str(current_task.request.id)
        notif_email = construct_notification_email(new_recip, new_subject, new_body, False)
        print(notif_email.__dict__)
    else:
        admin = User.objects.filter(id=1).first()
        event = Event.objects.filter(id=event_id).first()
        for recip in recipients:
            user = User.objects.filter(id=recip).first()
            Notification.objects.create(
                recipient=user, source=source, event=event, read=False, client_page=client_page,
                subject=subject, body=body, created_by=admin, modified_by=admin)
            # email: settings.EMAIL_WHISPERS, settings.EMAIL_NWHC_EPI
        if send_email and email_to is not None:
            for recip in email_to:
                notif_email = construct_notification_email(recip, subject, body, True)
                print(notif_email.__dict__)
    return True