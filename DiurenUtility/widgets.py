from django.forms import ClearableFileInput


class BootstrapClearableFileInput(ClearableFileInput):
    template_name = 'utility/bootstrap_clearable_file_input.html'

    def __init__(self, attrs=None, ignore_initial=False):
        super().__init__(attrs=attrs)
        self.ignore_initial = ignore_initial

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget'].update({
            'id': name + '_id'
        })
        if self.ignore_initial:
            context['widget'].update(
                {'is_initial': False}
            )
        return context
