from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models


# 学院
class College(models.Model):
    name = models.CharField(max_length=50, verbose_name='名称')

    class Meta:
        verbose_name = '学院'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


# 用户管理器
class UserManager(BaseUserManager):
    def _create_user(self, username, password, **extra_fields):
        if not username:
            raise ValueError('必须输入用户名')
        username = self.model.normalize_username(username)
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(username, password, **extra_fields)

    def create_superuser(self, username, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('type', 0)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(username, password, **extra_fields)


# 用户
class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(
        max_length=20,
        help_text='请输入20个以下的数字或字母组成的用户名',
        validators=[UnicodeUsernameValidator()],
        unique=True,
        verbose_name='用户名'
    )
    TYPE_CHOICE = (
        (0, '管理员'),
        (1, '学生'),
        (2, '团学组织'),
        (3, '社团')
    )
    type = models.PositiveSmallIntegerField(
        choices=TYPE_CHOICE,
        default=1,
        verbose_name='用户类型'
    )
    name = models.CharField(
        max_length=50,
        verbose_name='名称'
    )
    CAMPUS_CHOICE = (
        (0, '跨校区'),
        (1, '八里台'),
        (2, '津南'),
        (3, '泰达'),
    )
    campus = models.PositiveSmallIntegerField(
        choices=CAMPUS_CHOICE,
        default=0,
        verbose_name='校区'
    )
    college = models.ForeignKey(
        to=College,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name='学院'
    )
    description = models.TextField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='描述'
    )
    organizations = models.ManyToManyField(
        to='self',
        blank=True,
        related_name='members',
        symmetrical=False,
        help_text='可添加多个；组织关系不递归，间接上级组织需另外添加。',
        verbose_name='上级组织',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='是否启用'
    )
    is_staff = models.BooleanField(
        default=True,
        verbose_name='是否允许登录'
    )

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['name']

    objects = UserManager()

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return str(self.name) + '(' + str(self.get_type_display()) + ')'
