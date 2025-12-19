from datetime import date

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.forms import PasswordResetForm as PswResetForm
from django.contrib.auth.forms import SetPasswordForm as SetPswForm
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()

input_class = {"class": "form-control"}
select_class = {"class": "form-select"}

__invalid_login_error_message = (
    "Неверное имя пользователя/адрес электронной "
    "почты или пароль. Проверьте правильность ввода."
)

error_messages = {
    "required": {"required": "Это поле является обязательным"},
    "min_length": {
        "min_length": "Введённый пароль слишком короткий. Он должен содержать как минимум 8 символов"
    },
    "invalid_login": {"invalid_login": __invalid_login_error_message},
    "no_active_account": {"no_active_account": __invalid_login_error_message},
}


class LoginUserForm(AuthenticationForm):
    username = forms.CharField(
        label="E-mail или имя пользователя",
        widget=forms.TextInput(attrs={**input_class, "placeholder": "Логин"}),
        error_messages=error_messages["required"],
    )
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={**input_class, "placeholder": "Пароль"}),
        error_messages=error_messages["required"],
    )
    error_messages = error_messages["invalid_login"]

    class Meta:
        model = User
        fields = ("username", "password")

    def clean(self):
        res = super().clean()

        for field in self:
            if field.errors:
                field.field.widget.attrs["class"] += " is-invalid"

        return res


class RegisterUserForm(UserCreationForm):
    username = forms.CharField(
        label="Имя пользователя",
        widget=forms.TextInput(
            attrs={**input_class, "placeholder": "Имя пользователя"}
        ),
        error_messages=error_messages["required"],
    )
    password1 = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={**input_class, "placeholder": "Пароль"}),
        error_messages={**error_messages["required"], **error_messages["min_length"]},
        min_length=8,
    )
    password2 = forms.CharField(
        label="Подтверждение пароля",
        widget=forms.PasswordInput(
            attrs={**input_class, "placeholder": "Подтверждение пароля"}
        ),
        error_messages=error_messages["required"],
    )

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "password1",
            "password2",
        )
        widgets = {
            "email": forms.EmailInput(
                attrs={**input_class, "placeholder": "Адрес электронной почты"}
            ),
            "first_name": forms.TextInput(attrs={**input_class, "placeholder": "Имя"}),
            "last_name": forms.TextInput(
                attrs={**input_class, "placeholder": "Фамилия"}
            ),
        }
        error_messages = {
            "email": error_messages["required"],
        }

    def _post_clean(self):
        super()._post_clean()

        for field in self:
            if field.errors:
                field.field.widget.attrs["class"] += " is-invalid"


class PasswordResetForm(PswResetForm):
    email = forms.EmailField(
        label="Адрес электронной почты",
        widget=forms.EmailInput(
            attrs={**input_class, "placeholder": "Адрес электронной почты"}
        ),
        error_messages=error_messages["required"],
    )

    def clean(self):
        res = super().clean()

        for field in self:
            if field.errors:
                field.field.widget.attrs["class"] += " is-invalid"

        return res


class SetPasswordForm(SetPswForm):
    new_password1 = forms.CharField(
        label="Новый пароль",
        widget=forms.PasswordInput(
            attrs={**input_class, "placeholder": "Новый пароль"}
        ),
        error_messages={**error_messages["required"], **error_messages["min_length"]},
        min_length=8,
    )
    new_password2 = forms.CharField(
        label="Подтверждение нового пароля",
        widget=forms.PasswordInput(
            attrs={**input_class, "placeholder": "Подтверждение нового пароля"}
        ),
        error_messages=error_messages["required"],
    )

    def clean(self):
        res = super().clean()

        for field in self:
            if field.errors:
                field.field.widget.attrs["class"] += " is-invalid"

        return res


class UpdateUserForm(forms.ModelForm):
    username = forms.CharField(
        disabled=True,
        label="Имя пользователя",
        widget=forms.TextInput(
            attrs={**input_class, "placeholder": "Имя пользователя"}
        ),
    )
    email = forms.CharField(
        disabled=True,
        label="Электронный адрес почты",
        widget=forms.TextInput(
            attrs={**input_class, "placeholder": "Электронный адрес почты"}
        ),
    )

    class Meta:
        today = date.today()
        model = User
        fields = (
            "photo",
            "username",
            "email",
            "phone_number",
            "first_name",
            "last_name",
            "middle_name",
            "birth_date",
            "gender",
        )
        labels = {"photo": "Фотография:", "birth_date": "Дата рождения:"}
        widgets = {
            "photo": forms.FileInput(attrs=input_class),
            "phone_number": forms.TextInput(
                attrs={
                    **input_class,
                    "type": "tel",
                    "placeholder": "+7 (777) 777-77-77",
                }
            ),
            "first_name": forms.TextInput(attrs={**input_class, "placeholder": "Имя"}),
            "last_name": forms.TextInput(
                attrs={**input_class, "placeholder": "Фамилия"}
            ),
            "middle_name": forms.TextInput(
                attrs={**input_class, "placeholder": "Отчество"}
            ),
            "birth_date": forms.SelectDateWidget(
                attrs=select_class, years=tuple(range(today.year - 100, today.year - 9))
            ),
            "gender": forms.Select(attrs={**select_class, "placeholder": "Пол"}),
        }

    def clean(self):
        res = super().clean()

        for field in self:
            if field.errors:
                field.field.widget.attrs["class"] += " is-invalid"

        return res


class UserPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label="Старый пароль",
        widget=forms.PasswordInput(
            attrs={**input_class, "placeholder": "Старый пароль"}
        ),
        error_messages=error_messages["required"],
    )
    new_password1 = forms.CharField(
        label="Новый пароль",
        widget=forms.PasswordInput(
            attrs={**input_class, "placeholder": "Новый пароль"}
        ),
        error_messages={**error_messages["required"], **error_messages["min_length"]},
        min_length=8,
    )
    new_password2 = forms.CharField(
        label="Подтверждение нового пароля",
        widget=forms.PasswordInput(
            attrs={**input_class, "placeholder": "Подтверждение нового пароля"}
        ),
        error_messages=error_messages["required"],
    )

    def clean(self):
        res = super().clean()

        for field in self:
            if field.errors:
                field.field.widget.attrs["class"] += " is-invalid"

        return res
