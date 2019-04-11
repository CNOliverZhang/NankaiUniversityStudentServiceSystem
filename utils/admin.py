from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponseRedirect
from .models import *


# 学院管理
@admin.register(College)
class CollegeAdmin(admin.ModelAdmin):

    list_per_page = 10

    def has_module_permission(self, request):
        # 未登录用户无权限
        if isinstance(request.user, AnonymousUser):
            return False
        # 管理员有权限
        if request.user.type == ADMIN:
            return True
        # 学生无权限
        elif request.user.type == STUDENT:
            return False
        # 团学组织无权限
        elif request.user.type == ORGANIZATION:
            return False
        # 社团无权限
        elif request.user.type == CLUB:
            return False

    def has_view_permission(self, request, obj=None):
        # 管理员有权限
        if request.user.type == ADMIN:
            return True
        # 学生无权限
        elif request.user.type == STUDENT:
            return False
        # 团学组织无权限
        elif request.user.type == ORGANIZATION:
            return False
        # 社团无权限
        elif request.user.type == CLUB:
            return False

    def has_change_permission(self, request, obj=None):
        # 管理员有权限
        if request.user.type == ADMIN:
            return True
        # 学生无权限
        elif request.user.type == STUDENT:
            return False
        # 团学组织无权限
        elif request.user.type == ORGANIZATION:
            return False
        # 社团无权限
        elif request.user.type == CLUB:
            return False

    def has_add_permission(self, request, obj=None):
        # 管理员有权限
        if request.user.type == ADMIN:
            return True
        # 学生无权限
        elif request.user.type == STUDENT:
            return False
        # 团学组织无权限
        elif request.user.type == ORGANIZATION:
            return False
        # 社团无权限
        elif request.user.type == CLUB:
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
            # 自己
            if self.value() == '0':
                return queryset.filter(id=user.id)
            # 下属学生
            elif self.value() == '1':
                return (queryset.filter(type=STUDENT) & user.members.all()).exclude(id=user.id)
            # 下属组织和社团
            elif self.value() == '2':
                return ((queryset.filter(type=STUDENT) | queryset.filter(type=CLUB)) & user.members.all()).exclude(id=user.id)

    # 初始化列表页
    list_per_page = 10
    list_display = ('name', 'type', 'campus', 'college', 'description')
    list_filter = ('type', 'campus', Member)
    search_fields = ('username', 'name', 'college__name', 'organizations__name')
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
        # 管理员可查看全部信息
        if request.user.type == ADMIN:
            return qs
        # 学生可查看自身信息
        elif request.user.type == STUDENT:
            return qs.filter(id=request.user.id)
        # 团学组织可查看除管理员外的所有信息
        elif request.user.type == ORGANIZATION:
            return qs.exclude(type=ADMIN)
        # 社团可查看除管理员和团学组织外的所有信息
        elif request.user.type == CLUB:
            return qs.exclude(type=ADMIN).exclude(type=ORGANIZATION)

    # 用户模块权限
    def has_module_permission(self, request):
        # 未登录用户无权限
        if isinstance(request.user, AnonymousUser):
            return False
        # 管理员有权限
        if request.user.type == ADMIN:
            return True
        # 学生无权限
        elif request.user.type == STUDENT:
            return False
        # 团学组织有权限
        elif request.user.type == ORGANIZATION:
            return True
        # 社团有权限
        elif request.user.type == CLUB:
            return True

    # 新建用户权限
    def has_add_permission(self, request):
        # 管理员有权限
        if request.user.type == ADMIN:
            return True
        # 学生无权限
        elif request.user.type == STUDENT:
            return False
        # 团学组织有权限
        elif request.user.type == ORGANIZATION:
            return True
        # 社团无权限
        elif request.user.type == CLUB:
            return False

    # 修改账户权限
    def has_change_permission(self, request, obj=None):
        # 自己有权限
        if obj == request.user:
            return True
        # 管理员有权限
        if request.user.type == ADMIN:
            return True
        # 学生无权限
        elif request.user.type == STUDENT:
            return False
        # 团学组织无权限
        elif request.user.type == ORGANIZATION:
            return False
        # 社团无权限
        elif request.user.type == CLUB:
            return False

    # 删除账户权限
    def has_delete_permission(self, request, obj=None):
        # 管理员有权限
        if request.user.type == ADMIN:
            return True
        # 学生无权限
        elif request.user.type == STUDENT:
            return False
        # 团学组织无权限
        elif request.user.type == ORGANIZATION:
            return False
        # 社团无权限
        elif request.user.type == CLUB:
            return False

    # 根据用户角色决定下拉选单内容
    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == 'type':
            # 管理员允许创建所有用户角色
            if request.user.type == ADMIN:
                kwargs['choices'] = (
                    (0, '管理员'),
                    (1, '学生'),
                    (2, '团学组织'),
                    (3, '社团')
                )
            # 团学组织允许创建学生，团学组织或社团
            elif request.user.type == ORGANIZATION:
                kwargs['choices'] = (
                    (1, '学生'),
                    (2, '团学组织'),
                    (3, '社团')
                )
        return super(CustomUserAdmin, self).formfield_for_choice_field(db_field, request, **kwargs)

    # 根据用户角色变更增添页面内容
    def modify_add_form(self, request):
        # 管理员允许所有权限
        if request.user.type == ADMIN:
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
        elif request.user.type == ORGANIZATION:
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
        # 管理员拥有全部查看和修改权限
        if request.user.type == ADMIN:
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
        # 非管理员根据用户不同决定是否显示密码及只读字段
        else:
            # 学生不可更改用户名，用户类别和所属组织
            if request.user.type == STUDENT:
                self.readonly_fields = ('username', 'type', 'organizations')
            # 团学组织只可修改密码
            elif request.user.type == ORGANIZATION:
                self.readonly_fields = ('username', 'name', 'campus', 'college', 'type', 'organizations',)
            # 社团只可修改密码
            elif request.user.type == ORGANIZATION:
                self.readonly_fields = ('username', 'name', 'campus', 'college', 'type', 'organizations',)
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

    # 增加用户前设置表单字段
    def add_view(self, request, form_url='', extra_context=None):
        self.modify_add_form(request)
        return self.changeform_view(request, None, form_url, extra_context)

    # 进入修改页面前的行为
    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        obj = self.get_object(request, object_id)
        # 用户自己和管理员不显示添加进组织按钮
        if (obj != request.user) and (request.user.type != ADMIN):
            try:
                obj.organizations.get(id=request.user.id)
                extra_context['show_exclude'] = True
            except User.DoesNotExist:
                extra_context['show_include'] = True
        # 修改表单字段
        self.modify_change_form(request, obj)
        # 学生用户不显示面包屑导航防止进入基本管理页面
        if request.user.type == STUDENT:
            extra_context['show_breadcrumbs'] = False
        else:
            extra_context['show_breadcrumbs'] = True
        return self.changeform_view(request, object_id, form_url, extra_context)

    # 点击按钮
    def response_change(self, request, obj):
        # 管理员不拦截操作
        if request.user.type == ADMIN:
            pass
        # 学生编辑完自己的信息返回首页
        elif request.user.type == STUDENT:
            return HttpResponseRedirect("/")
        # 团学组织不拦截操作
        elif request.user.type == ORGANIZATION:
            pass
        # 社团不拦截操作
        elif request.user.type == CLUB:
            pass
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
        # 管理员不拦截操作
        if request.user.type == ADMIN:
            pass
        # 学生拦截操作
        elif request.user.type == STUDENT:
            self.message_user(request, "没有操作权限。")
            return
        # 团学组织不拦截操作
        elif request.user.type == ORGANIZATION:
            pass
        # 社团不拦截操作
        elif request.user.type == CLUB:
            pass
        for user in queryset:
            user.organizations.add(request.user)
        self.message_user(request, "已成功将这些用户添加进组织。")
    set_member.short_description = '批量添加进组织'

    # 批量删除从属关系操作
    def unset_member(self, request, queryset):
        # 管理员不拦截操作
        if request.user.type == ADMIN:
            pass
        # 学生拦截操作
        elif request.user.type == STUDENT:
            self.message_user(request, "没有操作权限。")
            return
        # 团学组织不拦截操作
        elif request.user.type == ORGANIZATION:
            pass
        # 社团不拦截操作
        elif request.user.type == CLUB:
            pass
        # 执行操作
        for user in queryset:
            user.organizations.remove(request.user)
        self.message_user(request, "已成功将这些用户移出组织。")
    unset_member.short_description = '批量移出组织'

    # 保存模型前的操作
    def save_model(self, request, obj, form, change):
        super(CustomUserAdmin, self).save_model(request, obj, form, change)
        # 自动添加上级组织
        if (not change) and (request.user.type != 0):
            obj.organizations.add(request.user)
