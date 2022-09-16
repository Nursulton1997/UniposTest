import datetime
from uuid import uuid4
import logging
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


# Create your models here.
class AccessToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.RESTRICT)
    access_token = models.CharField(max_length=200, unique=True)

    @classmethod
    def generate(cls, user: User):
        token = cls(user=user)
        token.access_token = f"{uuid4()}-{uuid4()}"
        token.save()
        return token.access_token

    def revoke(self):
        token = f"{uuid4()}-{uuid4()}"
        self.access_token = token
        self.save()
        return token

    def __str__(self):
        return self.user.username


class CreatedUpdated(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True)

    def save(self):
        self.updated_at = timezone.now()
        return super().save()

    class Meta:
        abstract = True


class Epos(CreatedUpdated):
    user = models.CharField(max_length=200, null=True)
    type = models.IntegerField(null=True)
    merchant = models.CharField(max_length=50, null=True)
    terminal = models.CharField(max_length=20, null=True)
    point_code = models.CharField(max_length=50, null=True)
    purpose = models.CharField(max_length=50, null=True)
    originator = models.CharField(max_length=50, null=True)
    center_id = models.CharField(max_length=50, null=True)
    status = models.BooleanField(default=False)


class Payments(CreatedUpdated):
    user = models.CharField(max_length=100, null=True)
    ext_id = models.CharField(max_length=250, null=True)


class Transfers(CreatedUpdated):
    user = models.CharField(max_length=100, null=True)
    ext_id = models.CharField(max_length=250, null=True)


class ToCard(CreatedUpdated):
    user = models.CharField(max_length=100, null=True)
    ext_id = models.CharField(max_length=250, null=True)
