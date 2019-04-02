from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.contrib.auth.admin import UserAdmin
from django.http import HttpResponseRedirect

from .models import *


# 学院管理
@admin.register(College)
class CollegeAdmin(admin.ModelAdmin):

    list_per_page = 10

    def get_model_perms(self, request):
        if request.user.type != 0:
            return {}
        return super().get_model_perms(request)

    def has_view_permission(self, request, obj=None):
        if request.user.type == 0:
            return True
        return False

    def has_change_permission(self, request, obj=None):
        if request.user.type == 0:
            return True
        return False

    def has_add_permission(self, request, obj=None):
        if request.user.type == 0:
            return True
        return False


# 用户管理
@admin.register(User)
class CustomUserAdmin(UserAdmin):

    # 自定义根据是否为成员筛选
    class Member(SimpleListFilter):
        title = '用户性质'
        parameter_name = 'member'

        def lookups(self, request, model_admin):
            return (
                ('0', '我自己'),
                ('1', '下属学生'),
                ('2', '下属组织')
            )

        def queryset(self, request, queryset):
            user = request.user
            if self.value() == '0':
                return queryset.filter(id=user.id)
            elif self.value() == '1':
                return (queryset.filter(type=1) & user.members.all()).exclude(id=user.id)
            elif self.value() == '2':
                return ((queryset.filter(type=2) | queryset.filter(type=3)) & user.members.all()).exclude(id=user.id)

    # 初始化列表页
    list_per_page = 10
    list_display = ('name', 'type', 'campus', 'college', 'description')
    list_filter = ('type', 'campus', Member)
    search_fields = ('username', 'name')
    actions = ['set_member', 'unset_member']

    # 初始化详情页全部权限
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('信息', {
            'fields': ('name', 'campus', 'college', 'description')
        }),
        ('用户角色', {
            'fields': ('type', 'organizations')
        })
    )
    add_fieldsets = (
        (None, {
            'fields': ('username', 'password1', 'password2')
        }),
        ('信息', {
            'fields': ('name', 'campus', 'college', 'description')
        }),
        ('用户角色', {
            'fields': ('type', 'organizations')
        })
    )
    filter_horizontal = ('organizations',)
    readonly_fields = ()

    # 根据用户角色筛选查询集
    def get_queryset(self, request):
        qs = super(CustomUserAdmin, self).get_queryset(request)
        # 学生可查看自身信息
        if request.user.type == 1:
            return qs.filter(id=request.user.id)
        # 团学组织可查看除管理员外的所有信息
        elif request.user.type == 2:
            return qs.exclude(type=0)
        # 社团可查看所有学生信息
        elif request.user.type == 3:
            return qs.filter(type=1) | qs.filter(id=request.user.id)
        # 管理员可查看全部用户信息
        else:
            return qs

    # 不允许学生显示列表页面
    def get_model_perms(self, request):
        if request.user.type == 1:
            return {}
        return super().get_model_perms(request)

    # 新建账户权限
    def has_add_permission(self, request):
        # 仅允许团学组织和管理员添加用户
        if (request.user.type == 0) or (request.user.type == 2):
            return True
        return False

    # 修改账户权限
    def has_change_permission(self, request, obj=None):
        # 不允许非管理员用户修改他人信息
        if (not request.user.type == 0) and obj and (obj != request.user):
            return False
        return True

    # 删除账户权限
    def has_delete_permission(self, request, obj=None):
        # 允许管理员删除任何用户，允许删除自身
        if request.user.type == 0 or (obj and (request.user == obj)):
            return True
        return False

    # 根据用户角色决定下拉选单内容
    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == 'type':
            # 管理员允许创建所有用户角色
            if request.user.type == 0:
                kwargs['choices'] = (
                    (0, '管理员'),
                    (1, '学生'),
                    (2, '团学组织'),
                    (3, '社团')
                )
            # 限制非管理员允许创建的用户角色
            else:
                kwargs['choices'] = (
                    (1, '学生'),
                    (2, '团学组织'),
                    (3, '社团')
                )
        return super(CustomUserAdmin, self).formfield_for_choice_field(db_field, request, **kwargs)

    # 根据用户角色变更增添页面内容
    def modify_add_form(self, request):
        # 管理员允许所有权限
        if request.user.type == 0:
            self.readonly_fields = ()
            self.add_fieldsets = (
                (None, {
                    'fields': ('username', 'password1', 'password2')
                }),
                ('信息', {
                    'fields': ('name', 'campus', 'college', 'description')
                }),
                ('用户角色', {
                    'fields': ('type', 'organizations')
                })
            )
        # 组织不可主动定义用户所属组织
        else:
            self.readonly_fields = ()
            self.add_fieldsets = (
                (None, {
                    'fields': ('username', 'password1', 'password2')
                }),
                ('信息', {
                    'fields': ('name', 'campus', 'college', 'description')
                }),
                ('用户角色', {
                    'fields': ('type',)
                })
            )

    # 根据用户角色变更修改页面内容
    def modify_change_form(self, request, obj):
        # 管理员拥有全部权限
        if request.user.type == 0:
            self.readonly_fields = ()
            self.fieldsets = (
                (None, {
                    'fields': ('username', 'password')
                }),
                ('信息', {
                    'fields': ('name', 'campus', 'college', 'description')
                }),
                ('用户角色', {
                    'fields': ('type', 'organizations')
                })
            )
            return
        # 有所属组织时显示所属组织一栏
        if len(obj.organizations.all()) == 0:
            # 自己访问时显示密码
            if obj == request.user:
                self.fieldsets = (
                    (None, {
                        'fields': ('username', 'password')
                    }),
                    ('信息', {
                        'fields': ('name', 'campus', 'college', 'description')
                    }),
                    ('用户角色', {
                        'fields': ('type',)
                    })
                )
            # 其他人访问时不显示密码
            else:
                self.fieldsets = (
                    ('信息', {
                        'fields': ('name', 'campus', 'college', 'description')
                    }),
                    ('用户角色', {
                        'fields': ('type',)
                    })
                )
        # 无所属组织时不显示所属组织一栏
        else:
            # 自己访问时显示密码
            if obj == request.user:
                self.fieldsets = (
                    (None, {
                        'fields': ('username', 'password')
                    }),
                    ('信息', {
                        'fields': ('name', 'campus', 'college', 'description')
                    }),
                    ('用户角色', {
                        'fields': ('type', 'organizations')
                    })
                )
            # 其他人访问时不显示密码
            else:
                self.fieldsets = (
                    ('信息', {
                        'fields': ('name', 'campus', 'college', 'description')
                    }),
                    ('用户角色', {
                        'fields': ('type', 'organizations')
                    })
                )
        # 学生不可更改用户名，用户类别和所属组织
        if request.user.type == 1:
            self.readonly_fields = ('username', 'type', 'organizations')
        # 组织和社团只可修改密码
        else:
            self.readonly_fields = ('username', 'name', 'campus', 'college', 'type', 'organizations',)

    # 增加用户前设置表单字段
    def add_view(self, request, form_url='', extra_context=None):
        self.modify_add_form(request)
        return self.changeform_view(request, None, form_url, extra_context)

    # 进入修改页面前的行为
    def change_view(self, request, object_id, form_url='', extra_context=None):
        # 修改按钮
        obj = self.get_object(request, object_id)
        if obj != request.user and request.user.type != 0:
            extra_context = extra_context or {}
            try:
                obj.organizations.get(id=request.user.id)
                extra_context['show_exclude'] = True
            except User.DoesNotExist:
                extra_context['show_include'] = True
        # 修改表单字段
        self.modify_change_form(request, obj)
        return self.changeform_view(request, object_id, form_url, extra_context)

    # 点击按钮
    def response_change(self, request, obj):
        # 添加进组织
        if "_include" in request.POST:
            obj.organizations.add(request.user)
            self.message_user(request, "已成功将此用户添加进组织。")
            return HttpResponseRedirect(".")
        # 移出组织
        elif "_exclude" in request.POST:
            obj.organizations.remove(request.user)
            self.message_user(request, "已成功将此用户移出组织。")
            return HttpResponseRedirect(".")
        return super().response_change(request, obj)

    # 批量添加从属关系操作
    def set_member(self, request, queryset):
        if request.user.type == 1:
            self.message_user(request, "没有相关权限。", 'warning')
        else:
            for user in queryset:
                user.organizations.add(request.user)
            self.message_user(request, "已成功将这些用户添加进组织。")
    set_member.short_description = '批量添加进组织'

    # 批量删除从属关系操作
    def unset_member(self, request, queryset):
        if request.user.type == 1:
            self.message_user(request, "没有相关权限。", 'warning')
        else:
            for user in queryset:
                user.organizations.remove(request.user)
            self.message_user(request, "已成功将这些用户移出组织。")
    unset_member.short_description = '批量移出组织'

    # 保存模型前的操作
    def save_model(self, request, obj, form, change):
        # 所有用户赋予登陆后台权限
        obj.is_superuser = True
        super(CustomUserAdmin, self).save_model(request, obj, form, change)
        # 自动添加上级组织
        if (not change) and (request.user.type != 0):
            obj.organizations.add(request.user)
