from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils import timezone
from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.utils.html import format_html
from .models import *


# 收集管理
@admin.register(Collecting)
class CollectingAdmin(admin.ModelAdmin):

    # 自定义筛选是否本人发布
    class UserPublishedFilter(SimpleListFilter):
        title = '发布者'
        parameter_name = 'user_published'

        def lookups(self, request, model_admin):
            return (
                ('0', '我发布的'),
                ('1', '其他人发布的'),
            )

        def queryset(self, request, queryset):
            # 自己发布的
            if self.value() == '0':
                return queryset.filter(publisher=request.user).all()
            # 非自己发布的
            elif self.value() == '1':
                return queryset.exclude(publisher=request.user).all()

    # 自定义筛选是否必须提交
    class UserForcedFilter(SimpleListFilter):
        title = '我是否需要提交'
        parameter_name = 'user_forced'

        def lookups(self, request, model_admin):
            return (
                ('0', '我不必提交'),
                ('1', '我必须提交'),
            )

        def queryset(self, request, queryset):
            # 自己必须提交的
            if self.value() == '0':
                forced_collectings = request.user.forced_collectings.distinct()
                for collecting in forced_collectings:
                    queryset = queryset.exclude(id=collecting.id)
                return queryset.distinct()
            # 自己不必提交的
            elif self.value() == '1':
                return (queryset.distinct() & request.user.forced_collectings.distinct()).distinct()

    # 自定义筛选是否超时
    class DueTimeMissedFilter(SimpleListFilter):
        title = '是否已过提交期限'
        parameter_name = 'due_time_missed'

        def lookups(self, request, modal_admin):
            return (
                ('0', '未设定提交期限'),
                ('1', '距离提交期限大于一周'),
                ('2', '距离提交期限不足一周'),
                ('3', '距离提交期限不足一天'),
                ('4', '距离提交期限不足一小时'),
                ('5', '已超过提交期限')
            )

        def queryset(self, request, queryset):
            current_time = timezone.now()
            # 未设定提交期限
            if self.value() == '0':
                return queryset.filter(due_time=None)
            # 大于一周
            elif self.value() == '1':
                time_point = current_time + timezone.timedelta(weeks=1)
                return queryset.filter(due_time__gte=time_point)
            # 小于一周
            elif self.value() == '2':
                time_point = current_time + timezone.timedelta(weeks=1)
                return queryset.filter(due_time__lte=time_point).filter(due_time__gte=current_time)
            # 小于一天
            elif self.value() == '3':
                time_point = current_time + timezone.timedelta(days=1)
                return queryset.filter(due_time__lte=time_point).filter(due_time__gte=current_time)
            # 小于一小时
            elif self.value() == '4':
                time_point = current_time + timezone.timedelta(hours=1)
                return queryset.filter(due_time__lte=time_point).filter(due_time__gte=current_time)
            # 已超时
            elif self.value() == '5':
                return queryset.filter(due_time__lte=current_time)

    # 自定义筛选我是否已提交
    class Submitted(SimpleListFilter):
        title = '我是否已提交'
        parameter_name = 'user_submitted'

        def lookups(self, request, modal_admin):
            return (
                ('0', '我未提交'),
                ('1', '我已提交')
            )

        def queryset(self, request, queryset):
            submittings = request.user.user_submittings.all()
            # 自己已提交
            if self.value() == '0':
                collectings = Collecting.objects.exclude(publisher=request.user)
                for submitting in submittings:
                    collectings = collectings.exclude(id=submitting.collecting.id)
                return queryset.distinct() & collectings.distinct()
            # 自己未提交
            elif self.value() == '1':
                collectings = Collecting.objects.none()
                for submitting in submittings:
                    collectings = collectings | Collecting.objects.filter(id=submitting.collecting.id)
                return queryset.distinct() & collectings.distinct()

    # 内容显示html
    def content_html(self, collecting):
        return format_html(collecting.content)
    content_html.short_description = '内容'

    # 初始化列表页
    list_per_page = 10
    list_display = ['title', 'publisher', 'publish_time', 'due_time', 'allow_multiple', 'private', 'forced']
    list_filter = [UserPublishedFilter, UserForcedFilter, DueTimeMissedFilter, Submitted, 'allow_multiple', 'private', 'forced']
    search_fields = ('title', 'content', 'publisher__name')

    # 初始化详情页
    fieldsets = (
        (None, {
            'fields': ('title', 'content', 'publisher', 'publish_time')
        }),
        ('提交限制', {
            'fields': ('due_time', 'allow_multiple', 'private', 'valid_users', 'forced', 'collect_from')
        })
    )
    filter_horizontal = ('valid_users', 'collect_from',)
    readonly_fields = ('publish_time',)

    # 重置查询集
    def get_queryset(self, request):
        qs = super(CollectingAdmin, self).get_queryset(request)
        # 管理员允许查看所有收集
        if request.user.type == User.ADMIN:
            return qs
        # 学生只允许查看公开的和有权限查看的收集
        elif request.user.type == User.STUDENT:
            return (qs.filter(private=False) | request.user.opened_collectings.all()).distinct()
        # 团学组织只允许查看自己创建的或公开的和有权限查看的收集
        elif request.user.type == User.ORGANIZATION:
            return (qs.filter(publisher=request.user) | qs.filter(private=False) | request.user.opened_collectings.all()).distinct()
        # 社团只允许查看自己创建的或公开的和有权限查看的收集
        elif request.user.type == User.CLUB:
            return (qs.filter(publisher=request.user) | qs.filter(private=False) | request.user.opened_collectings.all()).distinct()

    # 收集模块权限
    def has_module_permission(self, request):
        # 未登录用户无权限
        if isinstance(request.user, AnonymousUser):
            return False
        # 管理员有权限
        if request.user.type == User.ADMIN:
            return True
        # 学生有权限
        elif request.user.type == User.STUDENT:
            return True
        # 团学组织有权限
        elif request.user.type == User.ORGANIZATION:
            return True
        # 社团有权限
        elif request.user.type == User.CLUB:
            return True

    # 查看收集权限
    def has_view_permission(self, request, obj=None):
        # 管理员有权限
        if request.user.type == User.ADMIN:
            return True
        # 学生有权限
        elif request.user.type == User.STUDENT:
            return True
        # 团学组织有权限
        elif request.user.type == User.ORGANIZATION:
            return True
        # 社团有权限
        elif request.user.type == User.CLUB:
            return True

    # 新建收集权限
    def has_add_permission(self, request):
        # 管理员有权限
        if request.user.type == User.ADMIN:
            return True
        # 学生无权限
        elif request.user.type == User.STUDENT:
            return False
        # 团学组织有权限
        elif request.user.type == User.ORGANIZATION:
            return True
        # 社团有权限
        elif request.user.type == User.CLUB:
            return True

    # 修改收集权限
    def has_change_permission(self, request, obj=None):
        # 首页不显示编辑按钮
        if not obj:
            return False
        # 具体对象的编辑权限
        else:
            # 自己有权限
            if obj.publisher == request.user:
                return True
            # 管理员有权限
            if request.user.type == User.ADMIN:
                return True
            # 学生无权限
            elif request.user.type == User.STUDENT:
                return False
            # 团学组织无权限
            elif request.user.type == User.ORGANIZATION:
                return False
            # 社团无权限
            elif request.user.type == User.CLUB:
                return False

    # 删除收集权限
    def has_delete_permission(self, request, obj=None):
        # 自己有权限
        if obj and (obj.publisher == request.user):
            return True
        # 管理员有权限
        if request.user.type == User.ADMIN:
            return True
        # 学生无权限
        elif request.user.type == User.STUDENT:
            return False
        # 团学组织无权限
        elif request.user.type == User.ORGANIZATION:
            return False
        # 社团无权限
        elif request.user.type == User.CLUB:
            return False

    # 根据用户角色决定必须提交的用户可选列表
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == 'collect_from':
            # 管理员允许指定所有用户提交
            if request.user.type == User.ADMIN:
                kwargs["queryset"] = User.objects.all()
            # 非管理员只允许指定下级用户提交
            else:
                kwargs["queryset"] = request.user.members.all()
        elif db_field.name == 'valid_users':
            # 管理员允许指定所有用户查看
            if request.user.type == User.ADMIN:
                kwargs["queryset"] = User.objects.all()
            # 非管理员只允许指定非管理员用户查看
            else:
                kwargs["queryset"] = User.objects.exclude(type=User.ADMIN)
        return super(CollectingAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)

    # 根据用户角色变更添加页面的内容
    def modify_add_form(self, request):
        # 管理员允许自定义发布者
        if request.user.type == User.ADMIN:
            self.readonly_fields = ()
            self.fieldsets = (
                (None, {
                    'fields': ('title', 'content', 'publisher')
                }),
                ('提交限制', {
                    'fields': ('due_time', 'allow_multiple', 'private', 'valid_users', 'forced', 'collect_from')
                })
            )
        # 团学组织允许发布强制提交的收集
        elif request.user.type == User.ORGANIZATION:
            self.readonly_fields = ()
            self.fieldsets = (
                (None, {
                    'fields': ('title', 'content')
                }),
                ('提交限制', {
                    'fields': ('due_time', 'allow_multiple', 'private', 'valid_users', 'forced', 'collect_from')
                })
            )
        # 社团不允许发布强制提交的收集
        elif request.user.type == User.CLUB:
            self.readonly_fields = ()
            self.fieldsets = (
                (None, {
                    'fields': ('title', 'content')
                }),
                ('提交限制', {
                    'fields': ('due_time', 'allow_multiple', 'private', 'valid_users')
                })
            )

    # 根据用户角色变更修改页面的内容
    def modify_change_form(self, request, obj):
        # 管理员拥有一切查看和修改权限
        if request.user.type == User.ADMIN:
            self.readonly_fields = ('publish_time',)
            self.fieldsets = (
                (None, {
                    'fields': ('title', 'content', 'publisher', 'publish_time')
                }),
                ('提交限制', {
                    'fields': ('due_time', 'allow_multiple', 'private', 'valid_users', 'forced', 'collect_from')
                })
            )
        # 非管理员用户根据用户角色及是否为发布者决定权限
        else:
            # 发布者允许编辑
            if obj.publisher == request.user:
                # 团学组织允许发布强制收集
                if request.user.type == User.ORGANIZATION:
                    self.readonly_fields = ('publish_time',)
                    self.fieldsets = (
                        (None, {
                            'fields': ('title', 'content', 'publish_time')
                        }),
                        ('提交限制', {
                            'fields': ('due_time', 'allow_multiple', 'private', 'valid_users', 'forced', 'collect_from')
                        })
                    )
                # 社团不允许发布强制收集
                elif request.user.type == User.CLUB:
                    self.readonly_fields = ('publish_time',)
                    self.fieldsets = (
                        (None, {
                            'fields': ('title', 'content', 'publish_time')
                        }),
                        ('提交限制', {
                            'fields': ('due_time', 'allow_multiple', 'private', 'valid_users')
                        })
                    )
            # 非发布者只允许查看
            else:
                self.readonly_fields = ('title', 'content_html', 'publisher', 'publish_time', 'due_time',  'allow_multiple',)
                self.fieldsets = (
                    (None, {
                        'fields': ('title', 'content_html', 'publisher', 'publish_time')
                    }),
                    ('提交限制', {
                        'fields': ('due_time',  'allow_multiple',)
                    })
                )

    # 根据用户角色修改列表页内容
    def changelist_view(self, request, extra_context=None):
        # 有未提交内容时提示
        collectings = request.user.forced_collectings.all().filter(due_time__gte=timezone.now())
        for submitting in request.user.user_submittings.all():
            collectings = collectings.exclude(id=submitting.collecting.id)
        if len(collectings.all()) != 0:
            self.message_user(request, "你有必须提交但尚未提交的内容，请注意查看并及时提交。", 'warning')
        # 管理员的筛选器
        if request.user.type == User.ADMIN:
            self.list_display = ['title', 'publisher', 'publish_time', 'due_time', 'allow_multiple', 'private', 'forced']
            self.list_filter = [self.UserPublishedFilter, self.UserForcedFilter, self.DueTimeMissedFilter, self.Submitted, 'allow_multiple', 'private', 'forced']
        # 学生的筛选器
        elif request.user.type == User.STUDENT:
            self.list_display = ['title', 'publisher', 'publish_time', 'due_time', 'allow_multiple']
            self.list_filter = [self.UserForcedFilter, self.DueTimeMissedFilter, self.Submitted, 'allow_multiple']
        # 团学组织的筛选器
        elif request.user.type == User.ORGANIZATION:
            self.list_display = ['title', 'publisher', 'publish_time', 'due_time', 'allow_multiple', 'private', 'forced']
            self.list_filter = [self.UserPublishedFilter, self.UserForcedFilter, self.DueTimeMissedFilter, self.Submitted, 'allow_multiple', 'private', 'forced']
        # 社团的筛选器
        elif request.user.type == User.CLUB:
            self.list_display = ['title', 'publisher', 'publish_time', 'due_time', 'allow_multiple', 'private', 'forced']
            self.list_filter = [self.UserPublishedFilter, self.UserForcedFilter, self.DueTimeMissedFilter, self.Submitted, 'allow_multiple', 'private', 'forced']
        return super().changelist_view(request, extra_context)

    # 增加收集前设置表单字段
    def add_view(self, request, form_url='', extra_context=None):
        self.modify_add_form(request)
        return self.changeform_view(request, None, form_url, extra_context)

    # 修改收集前的操作
    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        obj = self.get_object(request, object_id)
        # 访问相关提交
        if 'related' in request.GET:
            # 获取所有相关提交
            submittings = Submitting.objects.filter(collecting=object_id)
            return_url = request.path
            # 显示指定用户的提交时将返回链接跳转回提交状态
            if 'user' in request.GET:
                submittings = submittings.filter(user=request.GET['user'])
                return_url = return_url + "?submit_status=1"
            # 非管理员且非发布者则只显示自己的相关提交
            if (obj.publisher != request.user) & (request.user.type != User.ADMIN):
                submittings = submittings.filter(user=request.user.id)
            # 由提交页面跳转来时返回链接将指向来源的提交
            if request.GET.get('from_subimtting'):
                return_url = "/CollectingAndSubmitting/submitting/" + str(request.GET['from_subimtting']) + "/change/"
            STATUS_CHOICE = ('草稿', '已提交', '已处理', '已驳回')
            results = [((
                s.title or '无标题',
                s.user,
                s.collecting,
                s.submit_time.strftime(u'%Y{y}%m{m}%d{d} %H:%M').format(y='年', m='月', d='日'),
                STATUS_CHOICE[s.status]
            ), (
                # 收集者查看草稿状态时无跳转链接
                None if ((s.status == Submitting.DRAFT) and (request.user == s.collecting.publisher))
                # 提交者或管理员显示草稿的跳转链接
                else ("/CollectingAndSubmitting/submitting/" + str(s.id) + "/change/"))
            ) for s in submittings]
            heads = ['标题', '提交者', '提交到', '提交时间', '提交状态', '操作']
            content = {
                "collecting_title": obj.title,
                "heads": heads,
                "rows": results,
                "return_url": return_url
            }
            return render(request, 'admin/CollectingAndSubmitting/CustomPages/related_list.html', content)
        # 查看强制提交的提交状态
        if 'submit_status' in request.GET:
            submitted = []
            not_submitted = []
            users = obj.collect_from.all()
            for user in users:
                if len(user.user_submittings.distinct() & obj.collecting_submittings.distinct()) != 0:
                    submitted.append(user)
                else:
                    not_submitted.append(user)
            TYPE_CHOICE = ('管理员', '学生', '团学组织', '社团')
            CAMPUS_CHOICE = ('跨校区', '八里台', '津南', '泰达', )
            submitted_results = [((
                u.name,
                TYPE_CHOICE[u.type],
                CAMPUS_CHOICE[u.campus],
                u.college or '-'
            ), (request.path + "?related=1&user=" + str(u.id))) for u in submitted]
            not_submitted_results = [(
                u.name,
                TYPE_CHOICE[u.type],
                u.campus or '无',
                u.college or '无'
            ) for u in not_submitted]
            submitted_heads = ['名称', '用户类型', '校区', '学院', '操作']
            not_submitted_heads = ['名称', '用户类型', '校区', '学院']
            return_url = "/CollectingAndSubmitting/collecting/" + str(object_id) + "/change/"
            content = {
                "collecting_title": obj.title,
                "submitted_heads": submitted_heads,
                "not_submitted_heads": not_submitted_heads,
                "submitted_results": submitted_results,
                "not_submitted_results": not_submitted_results,
                "return_url": return_url
            }
            return render(request, 'admin/CollectingAndSubmitting/CustomPages/collecting_submit_status.html', content)
        # 非发布者且非管理员则允许提交
        if (request.user != obj.publisher) and (request.user.type != User.ADMIN):
            # 未超时允许提交
            if (not obj.due_time) or obj.due_time > timezone.now():
                # 允许多份提交或尚未提交则显示新建提交按钮
                if obj.allow_multiple or len(obj.collecting_submittings.all() & request.user.user_submittings.all()) == 0:
                    extra_context['new_submit'] = True
                # 如果已有一个提交则显示修改提交按钮
                if len(obj.collecting_submittings.all() & request.user.user_submittings.all()) == 1:
                    submit = (obj.collecting_submittings.all() & request.user.user_submittings.all())[0].id
                    extra_context['modify_submit'] = "/CollectingAndSubmitting/submitting/" + str(submit) + "/change/"
                # 如果已有多个提交则显示提交列表按钮
                if len(obj.collecting_submittings.all() & request.user.user_submittings.all()) > 1:
                    extra_context['user_submit_list'] = request.path + "?related=1"
                # 如果已有提交则提示
                if len(obj.collecting_submittings.all() & request.user.user_submittings.all()) != 0:
                    self.message_user(request, "你已提交。")
                # 如果未提交且需要提交则警告
                else:
                    if obj.forced:
                        try:
                            request.user.forced_collectings.get(id=object_id)
                            self.message_user(request, "你必须提交这份材料但尚未提交，请注意及时提交。", 'warning')
                        except Collecting.DoesNotExist:
                            pass
            # 超时不允许提交
            else:
                # 如果已有提交则提示
                if len(obj.collecting_submittings.all() & request.user.user_submittings.all()) != 0:
                    self.message_user(request, "你已提交。")
                # 如果未提交，则根据是否强制决定显示内容
                else:
                    if obj.forced:
                        try:
                            request.user.forced_collectings.get(id=object_id)
                            self.message_user(request, "你必须提交这份材料但超时未提交，已无法提交。", 'error')
                        except Collecting.DoesNotExist:
                            self.message_user(request, "已超时，不允许提交。", 'warning')
                    else:
                        self.message_user(request, "已超时，不允许提交。", 'warning')
        # 发布者和管理员允许查看相关提交和提交情况
        if (request.user == obj.publisher) or (request.user.type == User.ADMIN):
            # 允许查看相关提交
            extra_context['collecting_submit_list'] = request.path + "?related=1"
            # 强制收集的提交显示收集状况
            if obj.forced:
                extra_context['submit_status'] = request.path + "?submit_status=1"
        # 设置表单字段
        self.modify_change_form(request, obj)
        return self.changeform_view(request, object_id, form_url, extra_context)

    # 点击按钮
    def response_change(self, request, obj):
        # 添加提交
        if "_add" in request.POST:
            submit = Submitting(collecting=obj, user=request.user)
            submit.save()
            submit_id = submit.id
            return HttpResponseRedirect("/CollectingAndSubmitting/submitting/" + str(submit_id) + "/change/")
        return super().response_change(request, obj)

    # 保存模型前的操作
    def save_model(self, request, obj, form, change):
        # 非管理员新建收集前自动添加发布者
        if request.user.type != User.ADMIN and (not change):
            obj.publisher = request.user
        # 管理员未填写发布者则自动添加
        if request.user.type == User.ADMIN and (not form.cleaned_data.get('publisher')):
            obj.publisher = request.user
        # 截止时间不允许早于发布时间
        if change and form.cleaned_data.get('due_time') and form.cleaned_data['due_time'] <= obj.publish_time:
            self.message_user(request, "修改时设置的截止时间不能早于发布时间，已清除截止时间。", 'warning')
            obj.due_time = None
        # 创建时截止时间不允许早于当前时间
        if (not change) and form.cleaned_data.get('due_time') and form.cleaned_data['due_time'] <= timezone.now():
            self.message_user(request, "创建时设置的截止时间不能早于当前时间，已清除截止时间。", 'warning')
            obj.due_time = None
        # 取消勾选指定用户查看时删除允许查看的用户
        if not form.cleaned_data.get('private'):
            form.cleaned_data['valid_users'] = []
        # 取消勾选强制提交时删除必须提交的用户
        if not form.cleaned_data.get('forced'):
            form.cleaned_data['collect_from'] = []
        # 允许查看的用户为空则取消勾选
        if (not form.cleaned_data.get('valid_users')) or (len(form.cleaned_data.get('valid_users')) == 0):
            obj.private = False
        # 强制提交的用户为空则取消勾选
        if (not form.cleaned_data.get('collect_from')) or (len(form.cleaned_data.get('collect_from')) == 0):
            obj.forced = False
        # 强制提交的用户不被允许查看则清除强制提交
        if form.cleaned_data.get('valid_users') and form.cleaned_data.get('collect_from'):
            if len(form.cleaned_data.get('collect_from').difference(form.cleaned_data.get('valid_users')).all()) != 0:
                self.message_user(request, "必须提交的用户需要有权限查看，已自动为相关用户添加查看权限。", 'warning')
                form.cleaned_data['valid_users'] = form.cleaned_data['valid_users'] | form.cleaned_data['collect_from']
        super(CollectingAdmin, self).save_model(request, obj, form, change)


# 提交管理
@admin.register(Submitting)
class SubmittingAdmin(admin.ModelAdmin):

    # 自定义根据提交关系筛选
    class Type(SimpleListFilter):
        title = '提交属性'
        parameter_name = 'submit_type'

        def lookups(self, request, modal_admin):
            return (
                ('0', '我提交的'),
                ('1', '提交给我的')
            )

        def queryset(self, request, queryset):
            if self.value() == '0':
                return queryset.filter(user=request.user)
            elif self.value() == '1':
                for submitting in queryset:
                    if submitting.collecting.publisher != request.user:
                        queryset = queryset.exclude(id=submitting.id)
                return queryset

    # 内容显示html
    def content_html(self, submitting):
        return format_html(submitting.content)
    content_html.short_description = '内容'

    # 初始化列表页
    list_per_page = 10
    list_display = ['title', 'user', 'collecting', 'submit_time', 'status']
    list_filter = [Type, 'status']
    search_fields = ('title', 'content', 'collecting__title', 'user__name')

    fieldsets = (
        (None, {
            'fields': ('title', 'collecting', 'content', 'file')
        }),
        ('相关信息', {
            'fields': ('user', 'submit_time', 'status')
        })
    )
    readonly_fields = ('collecting', 'user', 'submit_time', 'status')

    # 重置查询集
    def get_queryset(self, request):
        qs = super(SubmittingAdmin, self).get_queryset(request)
        # 管理员允许查看全部提交
        if request.user.type == User.ADMIN:
            return qs
        # 学生只允许查看自己的提交
        elif request.user.type == User.STUDENT:
            return (qs.distinct() & request.user.user_submittings.distinct()).distinct()
        # 团学组织只允许查看提交给自己的或自己的提交
        elif request.user.type == User.ORGANIZATION:
            user_submittings = qs.distinct() & request.user.user_submittings.distinct()
            for submitting in qs:
                if submitting.collecting.publisher != request.user:
                    qs = qs.exclude(id=submitting.id)
                qs = qs.exclude(status=Submitting.DRAFT)
            qs = (qs.distinct() | user_submittings).distinct()
            return qs
        # 社团只允许查看提交给自己的或自己的提交
        elif request.user.type == User.CLUB:
            user_submittings = qs.distinct() & request.user.user_submittings.distinct()
            for submitting in qs:
                if submitting.collecting.publisher != request.user:
                    qs = qs.exclude(id=submitting.id)
                qs = qs.exclude(status=Submitting.DRAFT)
            qs = (qs.distinct() | user_submittings).distinct()
            return qs

    # 提交模块权限
    def has_module_permission(self, request):
        # 未登录用户无权限
        if isinstance(request.user, AnonymousUser):
            return False
        # 管理员有权限
        if request.user.type == User.ADMIN:
            return True
        # 学生无权限
        elif request.user.type == User.STUDENT:
            return True
        # 团学组织有权限
        elif request.user.type == User.ORGANIZATION:
            return True
        # 社团有权限
        elif request.user.type == User.CLUB:
            return True

    # 查看提交权限
    def has_view_permission(self, request, obj=None):
        # 管理员有权限
        if request.user.type == User.ADMIN:
            return True
        # 学生有权限
        elif request.user.type == User.STUDENT:
            return True
        # 团学组织有权限
        elif request.user.type == User.ORGANIZATION:
            return True
        # 社团有权限
        elif request.user.type == User.CLUB:
            return True

    # 任何人都没有主动添加提交的权限
    def has_add_permission(self, request):
        # 管理员无权限
        if request.user.type == User.ADMIN:
            return False
        # 学生无权限
        elif request.user.type == User.STUDENT:
            return False
        # 团学组织无权限
        elif request.user.type == User.ORGANIZATION:
            return False
        # 社团无权限
        elif request.user.type == User.CLUB:
            return False

    # 修改提交的权限
    def has_change_permission(self, request, obj=None):
        # 首页不显示编辑按钮
        if not obj:
            return False
        # 具体对象的编辑权限
        else:
            # 自己有权限修改草根或被驳回的提交
            if obj.user == request.user:
                if obj.status == Submitting.DRAFT or obj.status == Submitting.REJECTED:
                    return True
                else:
                    return False
            # 管理员有权限
            if request.user.type == User.ADMIN:
                return True
            # 学生无权限
            elif request.user.type == User.STUDENT:
                return False
            # 团学组织无权限
            elif request.user.type == User.ORGANIZATION:
                return False
            # 社团无权限
            elif request.user.type == User.CLUB:
                return False

    # 除管理员外任何人都只可删除自己的提交
    def has_delete_permission(self, request, obj=None):
        # 自己有权限删除未批准的提交
        if obj and (obj.user == request.user):
            if obj.status != Submitting.HANDLED:
                return False
            else:
                return True
        # 管理员有权限
        if request.user.type == User.ADMIN:
            return True
        # 学生无权限
        elif request.user.type == User.STUDENT:
            return False
        # 团学组织无权限
        elif request.user.type == User.ORGANIZATION:
            return False
        # 社团无权限
        elif request.user.type == User.CLUB:
            return False

    # 根据用户角色变更修改页面的内容
    def modify_change_form(self, request, obj):
        # 管理员拥有一切查看和修改权限
        if request.user.type == User.ADMIN:
            self.readonly_fields = ('submit_time',)
        # 非管理员根据是否为提交者决定权限
        else:
            # 添加者可以编辑
            if obj.user == request.user:
                self.readonly_fields = ('collecting', 'user', 'submit_time', 'status')
            # 非自己的提交不允许修改
            else:
                self.readonly_fields = ('title', 'collecting', 'content_html', 'file', 'user', 'submit_time', 'status')

    # 根据用户角色修改列表页内容
    def changelist_view(self, request, extra_context=None):
        # 有被驳回的提交时提醒
        if len(request.user.user_submittings.filter(status=Submitting.REJECTED)) != 0:
            self.message_user(request, "你有被驳回的提交，请及时修改并重新提交。", 'warning')
        # 管理员的筛选器
        if request.user.type == User.ADMIN:
            self.list_filter = [self.Type, 'status']
        # 学生的筛选器
        elif request.user.type == User.STUDENT:
            self.list_filter = ['status']
        # 团学组织的筛选器
        if request.user.type == User.ORGANIZATION:
            self.list_filter = [self.Type, 'status']
        # 社团的筛选器
        if request.user.type == User.CLUB:
            self.list_filter = [self.Type, 'status']
        return super().changelist_view(request, extra_context)

    # 修改收集前的操作
    def change_view(self, request, object_id, form_url='', extra_context=None):
        obj = self.get_object(request, object_id)
        extra_context = extra_context or {}
        # 自己可以提交或撤回
        if obj.user == request.user:
            # 未提交时允许提交
            if obj.status == Submitting.DRAFT:
                extra_context['allow_submit'] = True
            # 已提交未处理时允许撤回
            elif obj.status == Submitting.SUBMITTED:
                extra_context['allow_withdraw'] = True
            # 该用户有多于一个提交时显示相关提交
            if len(Submitting.objects.filter(collecting=obj.collecting).filter(user=request.user)) > 1:
                extra_context['user_submit_list'] = "/CollectingAndSubmitting/collecting/" + str(obj.collecting.id) + "/change/?related=1&from_subimtting=" + str(obj.id)
        # 发布者允许处理或驳回
        elif obj.collecting.publisher == request.user:
            # 允许处理和驳回
            if obj.status == Submitting.SUBMITTED:
                extra_context['allow_handle'] = True
            # 显示更多提交
            extra_context['collecting_submit_list'] = "/CollectingAndSubmitting/collecting/" + str(obj.collecting.id) + "/change/?related=1&from_subimtting=" + str(obj.id)
        # 显示对应的收集
        extra_context['collecting'] = "/CollectingAndSubmitting/collecting/" + str(obj.collecting.id) + "/change/"
        # 设置表单字段
        self.modify_change_form(request, obj)
        return self.changeform_view(request, object_id, form_url, extra_context)

    # 点击按钮
    def response_change(self, request, obj):
        # 提交
        if "_submit" in request.POST:
            obj.status = Submitting.SUBMITTED
            obj.save()
            self.message_user(request, "提交成功，等待处理中。提交的内容被处理前你仍可以撤回并修改后重新提交。")
            return HttpResponseRedirect(request.path)
        # 撤回
        elif "_withdraw" in request.POST:
            obj.status = Submitting.DRAFT
            obj.save()
            self.message_user(request, "撤回成功，当前内容为草稿状态。再次提交前你可以继续修改。")
            return HttpResponseRedirect(request.path)
        # 处理
        elif "_handle" in request.POST:
            obj.status = Submitting.HANDLED
            obj.save()
            self.message_user(request, "标记完成，提交者将得到反馈。")
            return HttpResponseRedirect(request.path)
        # 驳回
        elif "_reject" in request.POST:
            obj.status = Submitting.REJECTED
            obj.save()
            self.message_user(request, "已驳回，提交者将得到反馈。")
            return HttpResponseRedirect("/CollectingAndSubmitting/submitting/")
        return super().response_change(request, obj)

    # 保存模型前的操作
    def save_model(self, request, obj, form, change):
        if change and request.user.type != User.ADMIN:
            obj.status = Submitting.DRAFT
        super(SubmittingAdmin, self).save_model(request, obj, form, change)
