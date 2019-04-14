import random
import re
from django import forms
from .models import *


# 注册表单
class RegisterForm(forms.ModelForm):
    # 随机选取反机器人答案
    def __init__(self, *args, **kwargs):
        print(kwargs['seed'])
        super(RegisterForm, self).__init__(*args, **kwargs)
        if len(AntiRobot.objects.all()) == 0:
            self.fields['anti_robot'].label = '南开大学创立于哪一年'
            self.fields['anti_robot'].widget.attrs['placeholder'] = '请输入四位阿拉伯数字'
            self.answer = '1919'
        else:
            anti_robot = AntiRobot.objects.all()[random.randint(0, len(AntiRobot.objects.all()) - 1)]
            self.fields['anti_robot'].label = anti_robot.question
            self.fields['anti_robot'].widget.attrs['placeholder'] = anti_robot.hint
            self.answer = anti_robot.answer
            print(self.fields['anti_robot'].label)
            print(self.answer)

    # 覆写用户名
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'required': True
            }
        ),
        max_length=20,
        error_messages={
            'invalid': None
        },
        label='学号'
    )
    # 覆写姓名
    name = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'required': True
            }
        ),
        max_length=50,
        label='姓名'
    )
    # 覆写密码
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'placeholder': '密码长度需在8位及以上',
                'required': True
            }
        ),
        min_length=8,
        max_length=128,
        label='密码'
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'placeholder': '请重复上方输入的密码',
                'required': True
            }
        ),
        min_length=8,
        max_length=128,
        label='确认密码'
    )
    # 反机器人
    anti_robot = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'placeholder': '请重复上方输入的密码',
                'required': True
            }
        ),
        label='验证问题'
    )

    class Meta:
        model = User
        fields = ('username', 'name', 'password', 'campus', 'college')

    # 校验表单
    def clean(self):
        data = super(RegisterForm, self).clean()
        # 验证码
        if data.get('anti_robot') != self.answer:
            print(data.get('anti_robot'))
            print(self.answer)
            raise forms.ValidationError('验证码错误。')
        # 密码不一致
        if data.get('password') != data.get('password_confirm'):
            raise forms.ValidationError("密码输入不一致,请重试。")
        # 用户名校验
        if data.get('username'):
            # 用户名重复
            if len(User.objects.filter(username=data['username'])) != 0:
                raise forms.ValidationError("该学号已注册。")
            # 学号格式错误
            pattern = re.compile('^[0-9]{7}$')
            if not re.match(pattern, data['username']):
                raise forms.ValidationError("学号格式错误。")

    # 保存前添加用户类别和密码
    def save(self, commit=True):
        instance = super(RegisterForm, self).save(commit=False)
        instance.type = 1
        instance.set_password(self.cleaned_data['password'])
        if commit:
            instance.save()
        return instance
