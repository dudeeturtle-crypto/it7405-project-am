from django import forms


class LoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:border-indigo-500',
        'placeholder': 'Enter your email'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:border-indigo-500',
        'placeholder': 'Enter your password'
    }))


class SignUpForm(forms.Form):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={
        'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:border-indigo-500',
        'placeholder': 'Choose a username'
    }))
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:border-indigo-500',
        'placeholder': 'Enter your email'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:border-indigo-500',
        'placeholder': 'Create a password'
    }))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:border-indigo-500',
        'placeholder': 'Confirm password'
    }), label='Confirm Password')

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password')
        p2 = cleaned.get('password2')
        if p1 and p1 != p2:
            raise forms.ValidationError('Passwords must match')
        return cleaned
