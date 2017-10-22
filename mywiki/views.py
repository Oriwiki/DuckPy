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
import string
from collections import OrderedDict
import re
from random import choice
from django.views.generic.edit import CreateView
from django.contrib.auth.forms import UserCreationForm

# Create your views here.

def edit(request, title=None, section=0):
    if request.method == 'GET':
        if title == None:
            return redirect('/')
    
        if 'section' in request.GET:
            section = int(request.GET['section'])
        
        try:
            page = Page.objects.get(title=title)
        except ObjectDoesNotExist:
            return render(request, LocalSettings.default_skin + '/edit.html', {'title': title, 'text': "", 'preview': "", 'section': 0, 'function': 'edit'})
        else:
            if page.is_created == True:
                text = Revision.objects.filter(page=page.id).order_by('-id').first().text
            else:
                text = ""
            
        if section > 0:
            toc = NamuMarkParser(text, title).get_toc()
            try:
                text = toc[section - 1][3]
            except IndexError:
                section = 0
        
        return render(request, LocalSettings.default_skin + '/edit.html', {'title': title, 'text': text, 'preview': "", 'section': section, 'function': 'edit'})
        
    elif request.method == 'POST':
        # 미리보기
        if 'preview' in request.POST:
            soup = BeautifulSoup(NamuMarkParser(request.POST['text'], title).parse(), "html.parser")
            return render(request, LocalSettings.default_skin + '/edit.html', {'title': title,'text': request.POST['text'], 'preview': soup.prettify(), 'section': request.POST['section']})
    
        # 저장
        if title.startswith('DuckPy:'):
            namespace = 1
        elif title.startswith('파일:'):
            namespace = 3
        elif title.startswith('분류:'):
            namespace = 4
        elif title.startswith(LocalSettings.project_name + ':'):
            namespace = 5
        elif title.startswith('틀:'):
            namespace = 6
        else:
            namespace = 0
        
        text = request.POST['text']
        section = int(request.POST['section'])

        try:
            Page(title=title, namespace=namespace, is_created=True).save()
        except IntegrityError:
            page = Page.objects.get(title=title)
            if page.is_created == True:
                pro_revision = Revision.objects.filter(page=page.id).order_by('-id').first()
                
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
                
                
                rev = pro_revision.rev + 1
                increase = len(text) - len(pro_revision.text)
            else:
                rev = 1
                increase = len(text)
                page.is_created = True
                page.save()
        else:
            page = Page.objects.get(title=title)
            rev = 1
            increase = len(text)
            
        Revision(text=text, page=page, comment=request.POST['comment'], rev=rev, increase=increase).save()
        
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
                
        return redirect('/w/' + title + '?alert=successEdit')
        
def view(request, title=None, rev=0):
    if request.method == 'GET':
        if title == None:
            if request.path.startswith('/w/'):
                 return redirect('/')
            title = LocalSettings.project_name + ':' + LocalSettings.mainpage_title
            
        try:
            page = Page.objects.get(title=title)
        except ObjectDoesNotExist:
            if request.path.startswith('/w/'):
                return render(request, LocalSettings.default_skin + '/wiki.html', {'error': '해당 문서가 존재하지 않습니다.', 'title': title, 'function': 'view'}, status=404)
            else:
                Page(title=title, namespace=5, is_created=True).save()
                page = Page.objects.get(title=title)
                Revision(text='Hello, World!', page=page, comment='This is testing revision.', rev=1, increase=len('Hello, World!')).save()
              
        if 'rev' in request.GET:
            rev = request.GET['rev']        
              
        # 분류
        if page.namespace == 4:
            BASE_CODE, CHOSUNG = 44032, 588
            CHOSUNG_LIST = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
            categories = {'sub': {}, 'template': {}, 'page': {}, 'project': {}}
            
            for categorized_page_id in page.category.split(','):
                if categorized_page_id == '':
                    continue
                categorized_page = Page.objects.get(id=categorized_page_id)
                if categorized_page.namespace == 0:
                    if categorized_page.title.lower().startswith(tuple(string.ascii_lowercase)):
                        try:
                            categories['page'][categorized_page.title[0].lower()].append(categorized_page.title)
                        except KeyError:
                            categories['page'][categorized_page.title[0].lower()] = []
                            categories['page'][categorized_page.title[0].lower()].append(categorized_page.title)
                        categories['page'][categorized_page.title[0].lower()].sort(key=str.lower)
                    elif re.match('[ㄱ-ㅎㅏ-ㅣ가-힣]', categorized_page.title[0]):
                        char_code = ord(categorized_page.title[0]) - BASE_CODE
                        char1 = int(char_code / CHOSUNG)
                        try:
                            categories['page'][CHOSUNG_LIST[char1]].append(categorized_page.title)
                        except KeyError:
                            categories['page'][CHOSUNG_LIST[char1]] = []
                            categories['page'][CHOSUNG_LIST[char1]].append(categorized_page.title)
                        categories['page'][CHOSUNG_LIST[char1]].sort(key=str.lower)
                    else:
                        try:
                            categories['page']['etc'].append(categorized_page.title)
                        except KeyError:
                            categories['page']['etc'] = []
                            categories['page']['etc'].append(categorized_page.title)
                        categories['page']['etc'].sort(key=str.lower)
                elif categorized_page.namespace == 6:
                    if categorized_page.title[2:].lower().startswith(tuple(string.ascii_lowercase)):
                        try:
                            categories['template'][categorized_page.title[2:][0].lower()].append(categorized_page.title[2:])
                        except KeyError:
                            categories['template'][categorized_page.title[2:][0].lower()] = []
                            categories['template'][categorized_page.title[2:][0].lower()].append(categorized_page.title[2:])
                        categories['template'][categorized_page.title[2:][0].lower()].sort(key=str.lower)
                    elif re.match('[ㄱ-ㅎㅏ-ㅣ가-힣]', categorized_page.title[2:][0]):
                        char_code = ord(categorized_page.title[2:][0]) - BASE_CODE
                        char1 = int(char_code / CHOSUNG)
                        try:
                            categories['template'][CHOSUNG_LIST[char1]].append(categorized_page.title[2:])
                        except KeyError:
                            categories['template'][CHOSUNG_LIST[char1]] = []
                            categories['template'][CHOSUNG_LIST[char1]].append(categorized_page.title[2:])
                        categories['template'][CHOSUNG_LIST[char1]].sort(key=str.lower)
                    else:
                        try:
                            categories['template']['etc'].append(categorized_page.title[2:])
                        except KeyError:
                            categories['template']['etc'] = []
                            categories['template']['etc'].append(categorized_page.title[2:])
                        categories['template']['etc'].sort(key=str.lower)
                elif categorized_page.namespace == 4:
                    if categorized_page.title[3:].lower().startswith(tuple(string.ascii_lowercase)):
                        try:
                            categories['sub'][categorized_page.title[3:][0].lower()].append(categorized_page.title[3:])
                        except KeyError:
                            categories['sub'][categorized_page.title[3:][0].lower()] = []
                            categories['sub'][categorized_page.title[3:][0].lower()].append(categorized_page.title[3:])
                        categories['sub'][categorized_page.title[3:][0].lower()].sort(key=str.lower)
                    elif re.match('[ㄱ-ㅎㅏ-ㅣ가-힣]', categorized_page.title[3:][0]):
                        char_code = ord(categorized_page.title[3:][0]) - BASE_CODE
                        char1 = int(char_code / CHOSUNG)
                        try:
                            categories['sub'][CHOSUNG_LIST[char1]].append(categorized_page.title[3:])
                        except KeyError:
                            categories['sub'][CHOSUNG_LIST[char1]] = []
                            categories['sub'][CHOSUNG_LIST[char1]].append(categorized_page.title[3:])
                        categories['sub'][CHOSUNG_LIST[char1]].sort(key=str.lower)
                    else:
                        try:
                            categories['sub']['etc'].append(categorized_page.title[3:])
                        except KeyError:
                            categories['sub']['etc'] = []
                            categories['sub']['etc'].append(categorized_page.title[3:])
                        categories['sub']['etc'].sort(key=str.lower)
                elif categorized_page.namespace == 5:
                    if categorized_page.title[len(LocalSettings.project_name) + 1:].lower().startswith(tuple(string.ascii_lowercase)):
                        try:
                            categories['project'][categorized_page.title[len(LocalSettings.project_name):][0].lower()].append(categorized_page.title[len(LocalSettings.project_name) + 1:])
                        except KeyError:
                            categories['project'][categorized_page.title[len(LocalSettings.project_name) + 1:][0].lower()] = []
                            categories['project'][categorized_page.title[len(LocalSettings.project_name) + 1:][0].lower()].append(categorized_page.title[len(LocalSettings.project_name) + 1:])
                        categories['project'][categorized_page.title[len(LocalSettings.project_name) + 1:][0].lower()].sort(key=str.lower)
                    elif re.match('[ㄱ-ㅎㅏ-ㅣ가-힣]', categorized_page.title[len(LocalSettings.project_name) + 1:][0]):
                        char_code = ord(categorized_page.title[len(LocalSettings.project_name) + 1:][0]) - BASE_CODE
                        char1 = int(char_code / CHOSUNG)
                        try:
                            categories['project'][CHOSUNG_LIST[char1]].append(categorized_page.title[len(LocalSettings.project_name) + 1:])
                        except KeyError:
                            categories['project'][CHOSUNG_LIST[char1]] = []
                            categories['project'][CHOSUNG_LIST[char1]].append(categorized_page.title[len(LocalSettings.project_name) + 1:])
                        categories['project'][CHOSUNG_LIST[char1]].sort(key=str.lower)
                    else:
                        try:
                            categories['project']['etc'].append(categorized_page.title[len(LocalSettings.project_name) + 1:])
                        except KeyError:
                            categories['project']['etc'] = []
                            categories['project']['etc'].append(categorized_page.title[len(LocalSettings.project_name) + 1:])
                        categories['project']['etc'].sort(key=str.lower)
                        
            categories['page'] = OrderedDict(sorted(categories['page'].items()))
            categories['template'] = OrderedDict(sorted(categories['template'].items()))
            categories['sub'] = OrderedDict(sorted(categories['sub'].items()))
            categories['project'] = OrderedDict(sorted(categories['project'].items()))
            
            if page.is_created == True:
                if rev == 0:
                    revision = Revision.objects.filter(page=page.id).order_by('-id').first()
                else:
                    try:
                        revision = Revision.objects.get(page=page.id, rev=rev)
                    except ObjectDoesNotExist:
                        return render(request, LocalSettings.default_skin + '/wiki.html', {'error': '해당 리비전이 존재하지 않습니다.', 'title': title, 'function': 'view'}, status=404)
            
                soup = BeautifulSoup(NamuMarkParser(revision.text, title).parse(), 'html.parser')
                return render(request, LocalSettings.default_skin + '/wiki.html', {'parse': soup.prettify(), 'title': title, 'function': 'view', 'categories': categories})
            else:
                return render(request, LocalSettings.default_skin + '/wiki.html', {'error': '해당 페이지에 리비전이 존재하지 않습니다.', 'title': title, 'function': 'view', 'categories': categories}, status=404)
                
            
        if rev == 0:
            revision = Revision.objects.filter(page=page.id).order_by('-id').first()
        else:
            try:
                revision = Revision.objects.get(page=page.id, rev=rev)
            except ObjectDoesNotExist:
                return render(request, LocalSettings.default_skin + '/wiki.html', {'error': '해당 리비전이 존재하지 않습니다.', 'title': title, 'function': 'view'}, status=404)
                
        soup = BeautifulSoup(NamuMarkParser(revision.text, title).parse(), 'html.parser')
        return render(request, LocalSettings.default_skin + '/wiki.html', {'parse': soup.prettify(), 'title': title, 'function': 'view'})
        
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
            return render(request, LocalSettings.default_skin + '/diff.html', {'error': '해당 문서가 존재하지 않습니다.', 'title': title}, status=404)
            
        if not 'rev' in request.GET or not 'oldrev' in request.GET:
            return render(request, LocalSettings.default_skin + '/diff.html', {'error': '비교하려는 리비전이 제시되지 않았습니다.', 'title': title}, status=412)
            
        rev = request.GET['rev']
        oldrev = request.GET['oldrev']
        
        if rev == oldrev:
            return render(request, LocalSettings.default_skin + '/diff.html', {'error': '비교하려는 리비전이 같습니다.', 'title': title}, status=412)
            
        try:
            text = Revision.objects.get(page=page_id, rev=rev).text
        except ObjectDoesNotExist:
            return render(request, LocalSettings.default_skin + '/diff.html', {'error': '해당 리비전이 존재하지 않습니다.', 'title': title}, status=404)
            
        try:
            oldtext = Revision.objects.get(page=page_id, rev=oldrev).text
        except ObjectDoesNotExist:
            return render(request, LocalSettings.default_skin + '/diff.html', {'error': '해당 리비전이 존재하지 않습니다.', 'title': title}, status=404)
            
        if text == oldtext:
            return render(request, LocalSettings.default_skin + '/diff.html', {'diff': '동일합니다.', 'title': title})
            
        diff = difflib.HtmlDiff().make_table(oldtext.splitlines(True), text.splitlines(True),  context=True).replace(' nowrap="nowrap"', '')
        
        return render(request, LocalSettings.default_skin + '/diff.html', {'diff': diff, 'title': title})
        
def history(request, title=None):
    if request.method == 'GET':
        if title == None:
            return redirect('/')
            
        try:
            page_id = Page.objects.get(title=title).id
        except ObjectDoesNotExist:
            return render(request, LocalSettings.default_skin + '/history.html', {'error': '해당 문서가 존재하지 않습니다.', 'title': title, 'function': 'history'}, status=404)
            
        paginator = Paginator(Revision.objects.filter(page=page_id).order_by('-id').all(), 20)
        
        if not 'page' in request.GET:
            page = 1
        else:
            page = request.GET.get('page')
            
        try:
            historys = paginator.page(page)
        except EmptyPage:
            historys = paginator.page(paginator.num_pages)
            
        return render(request, LocalSettings.default_skin + '/history.html', {'historys': historys, 'title': title, 'page': int(page), 'num_pages': paginator.num_pages, 'function': 'history'})
        
def revert(request, title=None):
    if request.method == 'GET':
        if title == None:
            return redirect('/')
            
        if not 'rev' in request.GET:
            return render(request, LocalSettings.default_skin + '/revert.html', {'error': '되돌리려는 리비전이 제시되지 않았습니다.', 'title': title}, status=412)
            
        rev = request.GET['rev']
        
        try:
            page_id = Page.objects.get(title=title).id
        except ObjectDoesNotExist:
            return render(request, LocalSettings.default_skin + '/revert.html', {'error': '해당 문서가 존재하지 않습니다.', 'title': title}, status=404)
            
        try:
            text = Revision.objects.get(page=page_id, rev=rev).text
        except ObjectDoesNotExist:
            return render(request, LocalSettings.default_skin + '/revert.html', {'error': '해당 리비전이 존재하지 않습니다.', 'title': title}, status=404)
            
            
        return render(request, LocalSettings.default_skin + '/revert.html', {'title': title, 'rev': rev, 'text': text})
            
        
    elif request.method == 'POST':
        if title == None:
            return redirect('/')
            
        if not 'rev' in request.POST:
            return render(request, LocalSettings.default_skin + '/revert.html', {'error': '되돌리려는 리비전이 제시되지 않았습니다.', 'title': title}, status=412)
            
        rev = request.POST['rev']
        
        try:
            page = Page.objects.get(title=title)
        except ObjectDoesNotExist:
            return render(request, LocalSettings.default_skin + '/revert.html', {'error': '해당 문서가 존재하지 않습니다.', 'title': title, 'function': 'history'}, status=404)
            
        try:
            revert_revision = Revision.objects.get(page=page.id, rev=rev)
        except ObjectDoesNotExist:
            return render(request, LocalSettings.default_skin + '/revert.html', {'error': '해당 리비전이 존재하지 않습니다.', 'title': title}, status=404)
            
        pro_revision = Revision.objects.filter(page=page.id).order_by('-id').first()
        new_rev = pro_revision.rev + 1
        increase = len(revert_revision.text) - len(pro_revision.text)
            
        Revision(text=revert_revision.text, page=page, comment='r' + str(revert_revision.rev) + '으로 되돌림: ' + request.POST['comment'], rev=new_rev, increase=increase).save()
        
        return redirect('/w/' + title)
        
def random(request):
    my_ids = Page.objects.filter(is_deleted=False, is_created=True).values_list('id', flat=True)
    rand_ids = choice(list(my_ids))
    return redirect('/w/' + Page.objects.get(id=rand_ids).title)
        
        
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

        
class signup(CreateView):
    template_name = LocalSettings.default_skin + '/signup.html'
    form_class = UserCreationForm
    success_url = "/?alert=successSignup"
    