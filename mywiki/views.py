from django.shortcuts import render
from django.shortcuts import redirect
from django.http import HttpResponse, HttpResponseNotFound
from NamuMarkParser import NamuMarkParser
from bs4 import BeautifulSoup
from .models import *
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
import LocalSettings

# Create your views here.

def edit(request, title=None, section=0):
    if request.method == 'GET':
        if title == None:
            return redirect('/')
    
        if 'section' in request.GET:
            section = request.GET['section']
        
        try:
            page_id = Page.objects.get(title=title).id
        except ObjectDoesNotExist:
            text = ""
        else:
            text = Revision.objects.filter(page=page_id).order_by('-id').first().text
        
        return render(request, 'edit.html', {'title': title, 'text': text, 'preview': ""})
    elif request.method == 'POST':
        # 미리보기
        if 'preview' in request.POST:
            soup = BeautifulSoup(NamuMarkParser(request.POST['text'], title).parse(), "html.parser")
            return render(request, 'edit.html', {'title': title, 'text': request.POST['text'], 'preview': soup.prettify()})
    
        # 저장
        try:
            Page(title=title, namespace=0, is_created=True).save()
        except IntegrityError:
            page = Page.objects.get(title=title)
            rev = Revision.objects.filter(page=page.id).order_by('-id').first().rev + 1
        else:
            page = Page.objects.get(title=title)
            rev = 1
            
        Revision(text=request.POST['text'], page=page, comment=request.POST['comment'], rev=rev).save()
        
        # 분류
        now_category = set(NamuMarkParser(request.POST['text'], title).get_category())
        if rev > 1:
            pro_revision = Revision.objects.get(page=page.id, rev=rev - 1)
            pro_category = set(NamuMarkParser(pro_revision.text, title).get_category())
            for each_category in pro_category - now_category:
                each_category_page = Page.objects.get(title=each_category)
                each_category_page.category = each_category_page.category.replace(str(page.id) + ',', '')
                each_category_page.save()
            
            for each_category in now_category - pro_category:
                __save_category(each_category, page.id)
        else:
            for each_category in now_category:
                __save_category(each_category, page.id)
                
        return redirect('/w/' + title)
        
def view(request, title=None, rev=0):
    if request.method == 'GET':
        if title == None:
            if request.path.startswith('/w/'):
                 return redirect('/')
            title = LocalSettings.project_name + ':' + LocalSettings.mainpage_title
            
        try:
            page_id = Page.objects.get(title=title).id
        except ObjectDoesNotExist:
            if request.path.startswith('/w/'):
                return HttpResponseNotFound()
            else:
                Page(title=title, namespace=5, is_created=True).save()
                page = Page.objects.get(title=title)
                Revision(text='Hello, World!', page=page, comment='This is testing revision.', rev=1).save()
                page_id = page.id
                
        if 'rev' in request.GET:
            rev = request.GET['rev']        
                
        if rev == 0:
            input = Revision.objects.filter(page=page_id).order_by('-id').first().text
        else:
            try:
                input = Revision.objects.get(page=page_id, rev=rev).text
            except ObjectDoesNotExist:
                return HttpResponseNotFound()
                
        soup = BeautifulSoup(NamuMarkParser(input, title).parse(), 'html.parser')
        return render(request, 'wiki.html', {'parse': soup.prettify(), 'title': title})
        
def raw(request, title=None, rev=0):
    if request.method == 'GET':
        if title == None:
            return redirect('/')
            
        try:
            page_id = Page.objects.get(title=title).id
        except ObjectDoesNotExist:
            return HttpResponseNotFound()
            
        if 'rev' in request.GET:
            rev = request.GET['rev']
        
        if rev == 0:
            return HttpResponse(Revision.objects.filter(page=page_id).order_by('-id').first().text, content_type='text/plain; charset="utf-8"')
        else:
            try:
                return HttpResponse(Revision.objects.get(page=page_id, rev=rev).text, content_type='text/plain; charset="utf-8"')
            except ObjectDoesNotExist:
                return HttpResponseNotFound()
        
def __save_category(each_category, page_id):
    try:
        each_category_page = Page.objects.get(title=each_category)
    except ObjectDoesNotExist:
        Page(title=each_category, namespace=4, category=str(page_id) + ',', is_created=False).save()
    else:
        if each_category_page.category == None:
            each_category_page.category = str(page_id) + ','
        else:
            each_category_page.category += str(page_id) + ','
        each_category_page.save()
