from django.shortcuts import render
from django.shortcuts import redirect
from django.http import HttpResponse, HttpResponseNotFound
from NamuMarkParser import NamuMarkParser
from bs4 import BeautifulSoup
from .models import *
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
import LocalSettings
import difflib
from urllib.parse   import quote
from django.core.paginator import Paginator, EmptyPage

# Create your views here.

def edit(request, title=None, section=0):
    if request.method == 'GET':
        if title == None:
            return redirect('/')
    
        if 'section' in request.GET:
            section = int(request.GET['section'])
        
        try:
            page_id = Page.objects.get(title=title).id
        except ObjectDoesNotExist:
            return render(request, 'edit.html', {'title': title, 'text': "", 'preview': "", 'section': 0, 'urlencode': quote(title), 'project_name': LocalSettings.project_name, 'function': 'edit'})
        else:
            text = Revision.objects.filter(page=page_id).order_by('-id').first().text
            
        if section > 0:
            toc = NamuMarkParser(text, title).get_toc()
            try:
                text = toc[section - 1][3]
            except IndexError:
                section = 0
        
        return render(request, 'edit.html', {'title': title, 'text': text, 'preview': "", 'section': section, 'urlencode': quote(title), 'project_name': LocalSettings.project_name, 'function': 'edit'})
        
    elif request.method == 'POST':
        # 미리보기
        if 'preview' in request.POST:
            soup = BeautifulSoup(NamuMarkParser(request.POST['text'], title).parse(), "html.parser")
            return render(request, 'edit.html', {'title': title,'text': request.POST['text'], 'preview': soup.prettify(), 'section': request.POST['section'], 'urlencode': quote(title), 'project_name': LocalSettings.project_name})
    
        # 저장
        if title.startswith('DuckPy:'):
            namespace = 1
        elif title.startswith('파일:'):
            namespace = 3
        elif title.startswith('분류:'):
            namespace = 4
        elif title.startswith(LocalSettings.project_name + ':'):
            namespace = 5
        else:
            namespace = 0
        
        try:
            Page(title=title, namespace=namespace, is_created=True).save()
        except IntegrityError:
            page = Page.objects.get(title=title)
            pro_revision = Revision.objects.filter(page=page.id).order_by('-id').first()
            rev = pro_revision.rev + 1
        else:
            page = Page.objects.get(title=title)
            rev = 1
            
        text = request.POST['text']
        section = int(request.POST['section'])
        if section > 0:
            parser = NamuMarkParser(pro_revision.text, title)
            toc = parser.get_toc()
            text = parser.toc_before
            for idx, each_toc in enumerate(toc):
                text += '=' * each_toc[2]
                text += each_toc[1]
                text += '=' * each_toc[2]
                text += '\n'
                if idx == section - 1:
                    text += request.POST['text'] + '\n'
                else:
                    try:
                        text += each_toc[3]
                    except IndexError:
                        pass
        Revision(text=text, page=page, comment=request.POST['comment'], rev=rev).save()
        
        # 분류
        now_category = set(NamuMarkParser(text, title).get_category())
        if rev > 1:
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
        return render(request, 'wiki.html', {'parse': soup.prettify(), 'title': title, 'urlencode': quote(title), 'project_name': LocalSettings.project_name, 'function': 'view'})
        
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
                
def diff(request, title=None):
    if request.method == 'GET':
        if title == None:
            return redirect('/')
            
        try:
            page_id = Page.objects.get(title=title).id
        except ObjectDoesNotExist:
            return HttpResponseNotFound()
            
        if not 'rev' in request.GET or not 'oldrev' in request.GET:
            return HttpResponseNotFound()
            
        rev = request.GET['rev']
        oldrev = request.GET['oldrev']
            
        try:
            text = Revision.objects.get(page=page_id, rev=rev).text
        except ObjectDoesNotExist:
            return HttpResponseNotFound()
            
        try:
            oldtext = Revision.objects.get(page=page_id, rev=oldrev).text
        except ObjectDoesNotExist:
            return HttpResponseNotFound()
            
        diff = difflib.HtmlDiff().make_table(oldtext.splitlines(True), text.splitlines(True),  context=True).replace(' nowrap="nowrap"', '')
        
        return render(request, 'diff.html', {'diff': diff, 'title': title, 'urlencode': quote(title), 'project_name': LocalSettings.project_name})
        
def history(request, title=None):
    if request.method == 'GET':
        if title == None:
            return redirect('/')
            
        try:
            page_id = Page.objects.get(title=title).id
        except ObjectDoesNotExist:
            return HttpResponseNotFound()
            
        paginator = Paginator(Revision.objects.filter(page=page_id).order_by('-id').all(), 20)
        
        if not 'page' in request.GET:
            page = 1
        else:
            page = request.GET.get('page')
            
        try:
            historys = paginator.page(page)
        except EmptyPage:
            historys = paginator.page(paginator.num_pages)
            
        return render(request, 'history.html', {'historys': historys, 'title': title, 'urlencode': quote(title), 'project_name': LocalSettings.project_name, 'page': int(page), 'num_pages': paginator.num_pages, 'function': 'history'})
        
        
        
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
