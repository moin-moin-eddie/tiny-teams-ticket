from django import forms


class CreateTicketForm(forms.Form):
    title = forms.CharField(
        label='Titel',
        required=False,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'name': 'title',
                'placeholder': 'Titel (nicht erforderlich)'
            }
        )
    )

    note = forms.CharField(
        label='Problembeschreibung',
        required=True,
        widget=forms.Textarea(
            attrs={'class': 'summernote',
                   'name': 'note',
                   'id': 'compose-textarea'
                   }
        )
    )

    files = forms.FileField(
        label='Datei hochladen',
        required=False,
        widget=forms.ClearableFileInput(
            attrs={
                'class': 'custom-file-input',
                'multiple': True,
                'id': 'attachments',
                'name': 'attachments'
            }
        )
    )


class PauseTicketForm(forms.Form):
    paused_until = forms.DateTimeField(
        label='Bis wann pausieren?'
    )


class SearchUsersForm(forms.Form):
    name = forms.CharField(
        label='',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control form-control-sm',
                'id': 'name',
                'name': 'name',
                'placeholder': '',
                'type': 'input'
            }
        )
    )
