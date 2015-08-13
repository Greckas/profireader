from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from ..models.users import User


def DR():
    print('DataRequired=',  dir(DataRequired()))
    print('DataRequired=',  ((DataRequired()).message))
    return DataRequired()

class LoginForm(Form):
    email = StringField('Email', validators=[DR(), Length(1, 64),
                                             Email()])
    password = PasswordField('Password', validators=[DR()])
    #remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')


class RegistrationForm(Form):
    email = StringField('Email', validators=[DR(), Length(1, 64),
                                             Email()])
    displayname = StringField('displayname', validators=[
        DR(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                              'Usernames must have only '
                                              'letters, numbers, dots or '
                                              'underscores')])
    password = PasswordField('Password', validators=[
        DR(), EqualTo('password2', message='Passwords must match.')])
    password2 = PasswordField('Confirm password', validators=[DR()])
    submit = SubmitField('Register')

    def validate_email(self, field):
        if User.query.filter_by(profireader_email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_displayname(self, field):
        if User.query.filter_by(profireader_name=field.data).first():
            raise ValidationError('Username already in use.')


class ChangePasswordForm(Form):
    old_password = PasswordField('Old password', validators=[DR()])
    password = PasswordField('New password', validators=[
        DR(), EqualTo('password2', message='Passwords must match')])
    password2 = PasswordField('Confirm new password',
                              validators=[DR()])
    submit = SubmitField('Update Password')


class PasswordResetRequestForm(Form):
    email = StringField('Email', validators=[DR(), Length(1, 64),
                                             Email()])
    submit = SubmitField('Reset Password')


class PasswordResetForm(Form):
    email = StringField('Email', validators=[DR(), Length(1, 64),
                                             Email()])
    password = PasswordField('New Password', validators=[
        DataRequired(), EqualTo('password2', message='Passwords must match')])
    password2 = PasswordField('Confirm password', validators=[DataRequired()])
    submit = SubmitField('Reset Password')

    def validate_email(self, field):
        if User.query.filter_by(profireader_email=field.data).first() is None:
            raise ValidationError('Unknown email address.')


class ChangeEmailForm(Form):
    email = StringField('New Email', validators=[DR(), Length(1, 64),
                                                 Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Update Email Address')

    def validate_email(self, field):
        if User.query.filter_by(profireader_email=field.data).first():
            raise ValidationError('Email already registered.')
