from django.db import models

# Create your models here.
class Page(models.Model):
    title = models.CharField(unique=True, blank=False, max_length=255)
    namespace = models.PositiveIntegerField(blank=False)
    backlink = models.TextField(null=True)
    category = models.TextField(null=True)
    is_deleted = models.BooleanField(default=False)
    is_created = models.BooleanField(default=False)
    
class Revision(models.Model):
    text = models.TextField()
    createDate = models.DateTimeField(auto_now_add=True)
    comment = models.TextField(null=True)
    user = models.ForeignKey('auth.user', on_delete=models.SET_NULL, null=True)
    ip = models.ForeignKey('ip', on_delete=models.SET_NULL, null=True)
    page = models.ForeignKey('page', on_delete=models.CASCADE)
    rev = models.PositiveIntegerField(blank=False)
    increase = models.IntegerField(blank=False)
    
class Ip(models.Model):
    ip = models.CharField(unique=True, blank=False, max_length=15)
    
class Log(models.Model):
    type = models.PositiveIntegerField(blank=False)
    target = models.PositiveIntegerField(blank=False)
    comment = models.TextField(null=True)
    user = models.ForeignKey('auth.user', on_delete=models.SET_NULL, null=True)
    ip = models.ForeignKey('ip', on_delete=models.SET_NULL, null=True)
