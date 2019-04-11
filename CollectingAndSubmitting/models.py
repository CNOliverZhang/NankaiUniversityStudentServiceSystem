from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from ckeditor_uploader.fields import RichTextUploadingField
from utils.models import College, User


# 材料收集
class Collecting(models.Model):
    title = models.CharField(
        max_length=100,
        verbose_name='标题'
    )
    content = RichTextUploadingField(verbose_name='内容')
    file = models.FileField(
        blank=True,
        null=True,
        verbose_name='附件'
    )
    publisher = models.ForeignKey(
        to=User,
        blank=True,
        on_delete=models.CASCADE,
        verbose_name='发布者'
    )
    publish_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name='发布日期'
    )
    due_time = models.DateTimeField(
        blank=True,
        null=True,
        help_text='超过截止时间无法提交，若不设置截止时间表示随时可提交。',
        verbose_name='截止时间'
    )
    allow_multiple = models.BooleanField(
        help_text='若选中此项，将允许同一用户提交多份材料。',
        verbose_name='允许提交多份材料'
    )
    private = models.BooleanField(
        help_text='若选中此项，须在下方添加有权查看的用户。',
        verbose_name='仅限指定用户查看'
    )
    valid_users = models.ManyToManyField(
        to=User,
        blank=True,
        related_name='opened_collectings',
        help_text='必须勾选“仅限指定用户查看”；如果未勾选，保存时将清空选中的用户并设为允许所有用户查看。',
        verbose_name='有权限查看的用户'
    )
    forced = models.BooleanField(
        help_text='若选中此项，须在下方添加必须提交的用户。',
        verbose_name='强制要求提交'
    )
    collect_from = models.ManyToManyField(
        to=User,
        blank=True,
        related_name='forced_collectings',
        help_text='必须勾选“强制要求提交”；如果未勾选，保存时将清空选中的用户并设为非必须提交。',
        verbose_name='必须提交的用户'
    )

    class Meta:
        verbose_name = '材料收集'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.title


# 材料提交
class Submitting(models.Model):
    collecting = models.ForeignKey(
        to=Collecting,
        related_name='collecting_submittings',
        verbose_name='提交到',
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        to=User,
        related_name='user_submittings',
        verbose_name='提交者',
        on_delete=models.CASCADE
    )
    title = models.CharField(
        max_length=100,
        blank=False,
        null=True,
        verbose_name='标题'
    )
    content = RichTextUploadingField(
        blank=False,
        null=True,
        verbose_name='内容'
    )
    file = models.FileField(
        blank=True,
        null=True,
        verbose_name='附件'
    )
    submit_time = models.DateTimeField(
        auto_now=True,
        verbose_name='提交时间'
    )
    STATUS_CHOICE = (
        (0, '草稿'),
        (1, '已提交'),
        (2, '已处理'),
        (3, '已驳回')
    )
    status = models.PositiveSmallIntegerField(
        choices=STATUS_CHOICE,
        default=0,
        verbose_name='提交状态'
    )

    class Meta:
        verbose_name = '材料提交'
        verbose_name_plural = verbose_name

    def __str__(self):
        if self.title:
            return self.title
        else:
            return '未命名提交'


# 提交相关常量
DRAFT = 0
SUBMITTED = 1
HANDLED = 2
REJECTED = 3
