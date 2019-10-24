from aldryn_client import forms

class Form(forms.BaseForm):
    apy_key = forms.CharField(
        'Mandrill API key',
        required=True
    )
    template = forms.CharField(
        'default mandrill template',
        required=False
    )


    def to_settings(self, data, settings):
        settings['MANDRILL_API_KEY'] = data['apy_key']
        if data['template']:
            settings['MANDRILL_DEFAULT_TEMPLATE'] = data['template']


        return settings


