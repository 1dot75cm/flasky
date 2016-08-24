# coding: utf-8
from flask_wtf import Form
from wtforms import StringField, SubmitField
from wtforms.validators import Required

class NameForm(Form):
    '''姓名表单'''
    name = StringField('What is your name?', validators=[Required()])
    submit = SubmitField('Submit')
