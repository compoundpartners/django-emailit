from aldryn_client import forms

class Form(forms.BaseForm):
    apy_key = forms.CharField(
        'Mandrill API key',
        required=True
    )


    def to_settings(self, data, settings):
        settings['MANDRILL_API_KEY'] = data['apy_key']

        return settings


