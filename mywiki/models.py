from django.db import models

# Create your models here.
class Page(models.Model):
    title = models.CharField(unique=True, blank=False, max_length=255)
    backlink = models.TextField(null=True)
    category = models.TextField(null=True)
    is_deleted = models.BooleanField(default=False)
    
class Revision(models.Model):
    text = models.TextField()
    createDate = models.DateTimeField(auto_now_add=True, null=True)
    comment = models.TextField(null=True)
    user = models.ForeignKey('auth.user', on_delete=models.SET_NULL, null=True)
    ip = models.ForeignKey('ip', on_delete=models.SET_NULL, null=True)
    page = models.ForeignKey('page', on_delete=models.CASCADE, null=True)
    
class Ip(models.Model):
    ip = models.CharField(unique=True, blank=False, max_length=15)