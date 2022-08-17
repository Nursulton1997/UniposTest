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
