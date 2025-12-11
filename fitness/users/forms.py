from datetime import date

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    AuthenticationForm,
    UserCreationForm,
    PasswordResetForm as PswResetForm,
    SetPasswordForm as SetPswForm,
    PasswordChangeForm,
)

input_class = {"class": "form-control"}
select_class = {"class": "form-select"}

error_messages = {
    "password": {"required": "Укажите пароль - это обязательное поле."},
    "password_new": {"required": "Укажите новый пароль - это обязательное поле."},
    "password_old": {"required": "Укажите старый пароль - это обязательное поле."},
    "password_confirm": {
        "required": "Поле подтверждения пароля обязательно для заполнения."
    },
    "password_new_confirm": {
        "required": "Поле подтверждения нового пароля обязательно для заполнения."
    },
    "email": {"required": "Укажите адрес электронной почты - это обязательное поле."},
}


class LoginUserForm(AuthenticationForm):
    username = forms.CharField(
        label="E-mail или имя пользователя",
        widget=forms.TextInput(attrs={**input_class, "placeholder": "Логин"}),
        error_messages={
            "required": "Укажите E-mail или имя пользователя - это обязательное поле."
        },
    )
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={**input_class, "placeholder": "Пароль"}),
        error_messages=error_messages["password"],
    )
    error_messages = {
        "invalid_login": "Неверное имя пользователя/адрес электронной "
        "почты или пароль. Проверьте правильность ввода.",
    }

    class Meta:
        model = get_user_model()
        fields = ["username", "password"]

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
        error_messages={
            "required": "Укажите имя пользователя - это обязательное поле."
        },
    )
    password1 = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={**input_class, "placeholder": "Пароль"}),
        error_messages=error_messages["password"],
    )
    password2 = forms.CharField(
        label="Подтверждение пароля",
        widget=forms.PasswordInput(
            attrs={**input_class, "placeholder": "Подтверждение пароля"}
        ),
        error_messages=error_messages["password_confirm"],
    )

    class Meta:
        model = get_user_model()
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "password1",
            "password2",
        ]
        widgets = {
            "email": forms.EmailInput(
                attrs={**input_class, "placeholder": "Адрес электронной почты"}
            ),
            "first_name": forms.TextInput(attrs={**input_class, "placeholder": "Имя"}),
            "last_name": forms.TextInput(
                attrs={**input_class, "placeholder": "Фамилия"}
            ),
        }

    def _post_clean(self):
        super()._post_clean()

        for field in self:
            field.field.widget.attrs["class"] += (
                " is-invalid" if field.errors else " is-valid"
            )

            if field.field == self.fields["password2"] and field.errors:
                self.fields["password1"].widget.attrs["class"] = (
                    input_class["class"] + " is-invalid"
                )


class PasswordResetForm(PswResetForm):
    email = forms.EmailField(
        label="Адрес электронной почты",
        widget=forms.EmailInput(
            attrs={**input_class, "placeholder": "Адрес электронной почты"}
        ),
        error_messages=error_messages["email"],
    )

    def clean_email(self):
        email = self.cleaned_data["email"]
        if not get_user_model().objects.filter(email=email).exists():
            self.fields["email"].widget.attrs["class"] += " is-invalid"
            raise forms.ValidationError(
                "Пользователь с таким адресом электронной почты не существует."
            )

        return email

    def clean(self):
        res = super().clean()

        if self.errors:
            self.fields["email"].widget.attrs["class"] += " is-invalid"

        return res


class SetPasswordForm(SetPswForm):
    new_password1 = forms.CharField(
        label="Новый пароль",
        widget=forms.PasswordInput(
            attrs={**input_class, "placeholder": "Новый пароль"}
        ),
        error_messages=error_messages["password_new"],
    )
    new_password2 = forms.CharField(
        label="Подтверждение нового пароля",
        widget=forms.PasswordInput(
            attrs={**input_class, "placeholder": "Подтверждение нового пароля"}
        ),
        error_messages=error_messages["password_new_confirm"],
    )

    def clean(self):
        res = super().clean()

        if self.errors:
            self.fields["new_password1"].widget.attrs["class"] += " is-invalid"
            self.fields["new_password2"].widget.attrs["class"] += " is-invalid"

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
        model = get_user_model()
        fields = [
            "photo",
            "username",
            "email",
            "phone_number",
            "first_name",
            "last_name",
            "middle_name",
            "birth_date",
            "gender",
        ]
        labels = {"photo": "Фотография:", "birth_date": "Дата рождения:"}
        widgets = {
            "photo": forms.FileInput(attrs=input_class),
            "phone_number": forms.TextInput(
                attrs={
                    **input_class,
                    "type": "tel",
                    "placeholder": "+7 (777) 777 77-77",
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

    def _post_clean(self):
        res = super()._post_clean()

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
        error_messages=error_messages["password_old"],
    )
    new_password1 = forms.CharField(
        label="Новый пароль",
        widget=forms.PasswordInput(
            attrs={**input_class, "placeholder": "Новый пароль"}
        ),
        error_messages=error_messages["password_new"],
    )
    new_password2 = forms.CharField(
        label="Подтверждение нового пароля",
        widget=forms.PasswordInput(
            attrs={**input_class, "placeholder": "Подтверждение нового пароля"}
        ),
        error_messages=error_messages["password_new_confirm"],
    )

    def clean(self):
        res = super().clean()

        for field in self:
            if field.errors:
                field.field.widget.attrs["class"] += " is-invalid"

            if field.field == self.fields["new_password2"] and field.errors:
                self.fields["new_password1"].widget.attrs["class"] = (
                    input_class["class"] + " is-invalid"
                )

        return res
