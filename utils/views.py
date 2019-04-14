from django.contrib import messages
from django.contrib.auth.models import AnonymousUser
from django.shortcuts import redirect
from django.views.generic import FormView
from .forms import RegisterForm


# 注册视图
class RegisterView(FormView):
    template_name = 'admin/utils/CustomPages/register.html'
    form_class = RegisterForm
    success_url = '/'

    # 表单有效即提交
    def form_valid(self, form):
        form.save()
        return super(RegisterView, self).form_valid(form)

    # 已登录用户不允许注册
    def get(self, request, *args, **kwargs):
        if not isinstance(request.user, AnonymousUser):
            return redirect('/')
        else:
            return super(RegisterView, self).get(request, args, kwargs)

    # 注册成功提示
    '''
    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            messages.add_message(request, messages.SUCCESS, '注册成功，请登录。')
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
    '''
