from django import forms

class LoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'w-full p-2 border rounded-lg', 'placeholder': 'Email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'w-full p-2 border rounded-lg', 'placeholder': 'Password'}))

class ChatbotForm(forms.Form):
    prompt = forms.CharField(widget=forms.TextInput(attrs={'class': 'flex-grow border rounded-l-lg p-2 focus:outline-none', 'placeholder': 'Type your message here...'}))
