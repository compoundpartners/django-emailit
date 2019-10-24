# -*- coding: utf-8 -*-
import premailer

from email.utils import parseaddr
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import EmailMultiAlternatives
from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.html import linebreaks

import mandrill

from .utils import force_language, get_template_names

try:
    basestring
except NameError:
    # Python 3
    basestring = str


def construct_mailit_mail(recipients=None, context=None, template_base='mandrillit/email', subject=None, message=None, site=None,
                   subject_templates=None, body_templates=None, html_templates=None, from_email=None, language=None,
                   **kwargs):
    """
    usage:
    construct_mailit_mail(['my@email.com'], {'my_obj': obj}, template_base='myapp/emails/my_obj_notification').send()
    :param recipients: recipient or list of recipients
    :param context: context for template rendering
    :param template_base: the base template. '.subject.txt', '.body.txt' and '.body.html' will be added
    :param subject: optional subject instead of rendering it through a template
    :param message: optional message (will be inserted into the base email template)
    :param site: the site this is on. uses current site by default
    :param subject_templates: override the subject template
    :param body_templates: override the body template
    :param html_templates: override the html body template
    :param from_email: defaults to settings.DEFAULT_FROM_EMAIL
    :param language: the language that should be active for this email. defaults to currently active lang
    :param kwargs: kwargs to pass into the Email class
    :return:
    """
    language = language or translation.get_language()
    with force_language(language):
        recipients = recipients or []
        if isinstance(recipients, basestring):
            recipients = [recipients]
        from_email = from_email or settings.DEFAULT_FROM_EMAIL
        subject_templates = subject_templates or get_template_names(language, template_base, 'subject', 'txt')
        body_templates = body_templates or get_template_names(language, template_base, 'body', 'txt')
        html_templates = html_templates or get_template_names(language, template_base, 'body', 'html')

        if not context:
            context = {}

        site = site or Site.objects.get_current()
        context['site'] = site
        context['site_name'] = site.name
        protocol = 'https'  # TODO: this should come from settings
        base_url = "%s://%s" % (protocol, site.domain)
        if message:
            context['message'] = message

        subject = subject or render_to_string(subject_templates, context)
        subject = subject.replace('\n', '').replace('\r', '').strip()
        context['subject'] = subject
        try:
            html = render_to_string(html_templates, context)
        except TemplateDoesNotExist:
            html = ''
        else:
            html = premailer.transform(html, base_url=base_url)
        try:
            body = render_to_string(body_templates, context)
        except TemplateDoesNotExist:
            body = ''

        mail = EmailMultiAlternatives(subject, body, from_email, recipients, **kwargs)

        if not (body or html):
            # this is so a meaningful exception can be raised
            render_to_string([html_templates], context)
            render_to_string([body_templates], context)

        if html:
            mail.attach_alternative(html, 'text/html')
    return mail


def construct_mail(recipients=None, context=None, template_base='mandrillit/email', subject=None, message=None, site=None,
                   subject_templates=None, body_templates=None, html_templates=None, from_email=None, language=None,
                   **kwargs):
    """
    usage:
    construct_mailit_mail(['my@email.com'], {'my_obj': obj}, template_base='myapp/emails/my_obj_notification').send()
    :param recipients: recipient or list of recipients
    :param context: context for template rendering
    :param template_base: the base template. '.subject.txt', '.body.txt' and '.body.html' will be added
    :param subject: optional subject instead of rendering it through a template
    :param message: optional message (will be inserted into the base email template)
    :param site: the site this is on. uses current site by default
    :param subject_templates: override the subject template
    :param body_templates: override the body template
    :param html_templates: override the html body template
    :param from_email: defaults to settings.DEFAULT_FROM_EMAIL
    :param language: the language that should be active for this email. defaults to currently active lang
    :param kwargs: kwargs to pass into the Email class
    :return:
    """
    message = {}
    language = language or translation.get_language()
    with force_language(language):
        recipients = recipients or []
        if isinstance(recipients, basestring):
            recipients = [recipients]
        message['to'] = [{'email': parseaddr(recipient)[1], 'name': parseaddr(recipient)[0], 'type': 'to'} for recipient in recipients]
        from_email = parseaddr(from_email)
        message['from_email'] = from_email[1] or settings.DEFAULT_FROM_EMAIL
        subject_templates = subject_templates or get_template_names(language, template_base, 'subject', 'txt')
        body_templates = body_templates or get_template_names(language, template_base, 'body', 'txt')
        html_templates = html_templates or get_template_names(language, template_base, 'body', 'html')

        if not context:
            context = {}

        site = site or Site.objects.get_current()
        context['site'] = site
        context['site_name'] = site.name
        message['from_name'] = from_email[0] or site.name
        protocol = 'https'  # TODO: this should come from settings
        base_url = "%s://%s" % (protocol, site.domain)
        if message:
            context['message'] = message

        subject = subject or render_to_string(subject_templates, context)
        subject = subject.replace('\n', '').replace('\r', '').strip()
        context['subject'] = subject
        message['subject'] = subject
        try:
            body = render_to_string(body_templates, context)
        except TemplateDoesNotExist:
            body = ''
        message['text'] = body
        try:
            html = render_to_string(html_templates, context)
        except TemplateDoesNotExist:
            html = linebreaks(body)
        message['html'] = html
        message['full_html'] = premailer.transform(html, base_url=base_url)

        if not (body or html):
            # this is so a meaningful exception can be raised
            render_to_string([html_templates], context)
            render_to_string([body_templates], context)

    return message


def send_mail(*args, **kwargs):
    template_name = kwargs.pop('mandrill_template')
    message = construct_mail(*args, **kwargs)
    if not send_constructed_mail(message, template_name=template_name):
        construct_mailit_mail(*args, **kwargs).send()

def send_constructed_mail(message, template_name=None):
    try:
        mandrill_client = mandrill.Mandrill(settings.MANDRILL_API_KEY)

        if template_name:
            del message['full_html']
            return mandrill_client.messages.send_template(
                template_name=template_name,
                template_content=[{'name': 'main', 'content': message['html']}],
                message=message,
                async=False,
                ip_pool='Main Pool',
            )
        else:
            message['html'] = message['full_html']
            del message['full_html']
            return mandrill_client.messages.send(
                message=message,
                async=False,
                ip_pool='Main Pool',
            )
    except mandrill.Error as e:
        print('A mandrill error occurred: %s - %s' % (e.__class__, e))
        return False


def mail_admins(*args, **kwargs):
    return send_mail([a[1] for a in settings.ADMINS], *args, **kwargs)


def mail_managers(*args, **kwargs):
    return send_mail([a[1] for a in settings.MANAGERS], *args, **kwargs)
