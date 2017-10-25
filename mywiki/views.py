from django.shortcuts import render
from django.shortcuts import redirect
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from NamuMarkParser import NamuMarkParser
from bs4 import BeautifulSoup
from .models import *
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
import LocalSettings
import difflib
from urllib.parse   import quote, unquote
from django.core.paginator import Paginator, EmptyPage
import string
from collections import OrderedDict
import re
from random import choice
from django.views.generic.edit import CreateView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from ipware.ip import get_ip
from django.core.urlresolvers import reverse

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
            return render(request, LocalSettings.default_skin + '/edit.html', {'title': title, 'text': "", 'preview': "", 'section': 0})
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
        
        return render(request, LocalSettings.default_skin + '/edit.html', {'title': title, 'text': text, 'preview': "", 'section': section})
        
    elif request.method == 'POST':
        # 미리보기
        if 'preview' in request.POST:
            soup = BeautifulSoup(NamuMarkParser(request.POST['text'], title).parse(), "html.parser")
            return render(request, LocalSettings.default_skin + '/edit.html', {'title': title,'text': request.POST['text'], 'preview': soup.prettify(), 'section': request.POST['section']})
    
        # 저장
        
        namespace = __get_namespace(title)
        
        if namespace == 2:
            if not request.user.is_active or request.user.username != re.sub('\.(css|js)$', '', title[4:]):
                return render(request, LocalSettings.default_skin + '/edit.html', {'title': title,'text': request.POST['text'], 'section': request.POST['section'], 'error': '사용자 문서는 본인만 편집 가능합니다.'})
                
        # 사용자
        editor = __get_user(request)
        
        text = request.POST['text']
        
        try:
            Page(title=title, namespace=namespace, is_created=True).save()
        except IntegrityError:
            page = Page.objects.get(title=title)
            if page.is_created == True:
                pro_revision = Revision.objects.filter(page=page.id).order_by('-id').first()
                pro_parser = NamuMarkParser(pro_revision.text, title)
                
                # 단락 편집
                if section > 0:
                    toc = pro_parser.get_toc()
                    text = pro_parser.toc_before
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
                pro_parser = None
                page.is_created = True
                page.save()
        else:
            page = Page.objects.get(title=title)
            pro_parser = None
            rev = 1
            increase = len(text)
            
        Revision(text=text, page=page, comment=request.POST['comment'], rev=rev, increase=increase, user=editor['user'], ip=editor['ip']).save()
        
        now_parser = NamuMarkParser(text, title)
        
        __insert(now_parser, pro_parser, page.id, rev)
        
        return HttpResponseRedirect(reverse('view', kwargs={'title': title}) + '?alert=successEdit')
        
def view(request, title=None, rev=0):
    if request.method == 'GET':
        if title == None:
            if request.path.startswith('/w/'):
                 return redirect('/')
            title = LocalSettings.project_name + ':' + LocalSettings.mainpage_title
            
        try:
            page = Page.objects.get(title=title, is_deleted=False)
        except ObjectDoesNotExist:
            if Page.objects.all().count() > 0:
                return render(request, LocalSettings.default_skin + '/wiki.html', {'error': '해당 문서가 존재하지 않습니다.', 'title': title}, status=404)
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
            
            if page.category == None or page.category == "":
                return render(request, LocalSettings.default_skin + '/wiki.html', {'error': '분류가 존재하지 않습니다.', 'title': title})
                
            categories = list(filter(None, page.category.split(',')))
            
            paginator = Paginator(categories, 20)
            
            if not 'page' in request.GET:
                page_i = 1
            else:
                page_i = request.GET.get('page')
                
            try:
                category_ids = paginator.page(page_i)
            except EmptyPage:
                category_ids = paginator.page(paginator.num_pages)
                
            category_titles = [ [], [], [], [], [], [], [] ]
            for category_id in category_ids:
                categorized_page = Page.objects.get(pk=category_id, is_created=True, is_deleted=False)
                if categorized_page.namespace == 0:
                    category_titles[0].append(categorized_page.title)
                elif categorized_page.namespace == 1:
                    category_titles[1].append(categorized_page.title[7:])
                elif categorized_page.namespace == 2:
                    category_titles[2].append(categorized_page.title[4:])
                elif categorized_page.namespace == 3:
                    category_titles[3].append(categorized_page.title[3:])
                elif categorized_page.namespace == 4:
                    category_titles[4].append(categorized_page.title[3:])
                elif categorized_page.namespace == 5:
                    category_titles[5].append(categorized_page.title[len(LocalSettings.project_name) + 1:])
                elif categorized_page.namespace == 6:
                    category_titles[6].append(categorized_page.title[2:])
            
            categories = [ OrderedDict(), OrderedDict(), OrderedDict(), OrderedDict(), OrderedDict(), OrderedDict(), OrderedDict() ]
            BASE_CODE, CHOSUNG = 44032, 588
            CHOSUNG_LIST = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
            for j in range(0,7):
                category_titles[j].sort(key=str.lower)
                
                for categorized_title in category_titles[j]:
                    if categorized_title.lower().startswith(tuple(string.ascii_lowercase)):
                        try:
                            categories[j][categorized_title[0].upper()].append(categorized_title)
                        except KeyError:
                            categories[j][categorized_title[0].upper()] = [categorized_title]
                    elif re.match('[ㄱ-ㅎㅏ-ㅣ가-힣]', categorized_title[0]):
                        char_code = ord(categorized_title[0]) - BASE_CODE
                        char1 = int(char_code / CHOSUNG)
                        try:
                            categories[j][CHOSUNG_LIST[char1]].append(categorized_title)
                        except KeyError:
                            categories[j][CHOSUNG_LIST[char1]] = [categorized_title]
                    else:
                        try:
                            categories[j]['etc'].append(categorized_title)
                        except KeyError:
                            categories[j]['etc'] = [categorized_title]
                
                
            
            if page.is_created == True:
                if rev == 0:
                    revision = Revision.objects.filter(page=page.id).order_by('-id').first()
                else:
                    try:
                        revision = Revision.objects.get(page=page.id, rev=rev)
                    except ObjectDoesNotExist:
                        return render(request, LocalSettings.default_skin + '/wiki.html', {'error': '해당 리비전이 존재하지 않습니다.', 'title': title}, status=404)
            
                soup = BeautifulSoup(NamuMarkParser(revision.text, title).parse(), 'html.parser')
                return render(request, LocalSettings.default_skin + '/wiki.html', {'parse': soup.prettify(), 'title': title, 'categories': categories, 'page': int(page_i), 'num_pages': paginator.num_pages})
            else:
                return render(request, LocalSettings.default_skin + '/wiki.html', {'error': '문서에 리비전이 존재하지 않습니다.', 'title': title, 'categories': categories, 'page': int(page_i), 'num_pages': paginator.num_pages}, status=404)
            
        
        if page.is_created == False:
            return render(request, LocalSettings.default_skin + '/wiki.html', {'error': '해당 문서가 존재하지 않습니다.', 'title': title}, status=404)

        if rev == 0:
            revision = Revision.objects.filter(page=page.id).order_by('-id').first()
        else:
            try:
                revision = Revision.objects.get(page=page.id, rev=rev)
            except ObjectDoesNotExist:
                return render(request, LocalSettings.default_skin + '/wiki.html', {'error': '해당 리비전이 존재하지 않습니다.', 'title': title}, status=404)
                
        if revision.text.startswith(('#redirect ', '#넘겨주기 ')):
            if ('redirect' in request.GET and int(request.GET['redirect']) == 1) or not 'redirect' in request.GET:
                if revision.text.startswith('#redirect '):
                    return HttpResponseRedirect(reverse('view', kwargs={'title': revision.text[10:]}) + '?redirectFrom=' + quote(title))
                else:
                    return HttpResponseRedirect(reverse('view', kwargs={'title': revision.text[6:]}) + '?redirectFrom=' + quote(title))
                
        soup = BeautifulSoup(NamuMarkParser(revision.text, title).parse(), 'html.parser')
        return render(request, LocalSettings.default_skin + '/wiki.html', {'parse': soup.prettify(), 'title': title})
        
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
            return render(request, LocalSettings.default_skin + '/history.html', {'error': '해당 문서가 존재하지 않습니다.', 'title': title}, status=404)
            
        paginator = Paginator(Revision.objects.filter(page=page_id).order_by('-id').all(), 20)
        
        if not 'page' in request.GET:
            page = 1
        else:
            page = request.GET.get('page')
            
        try:
            historys = paginator.page(page)
        except EmptyPage:
            historys = paginator.page(paginator.num_pages)
            
        return render(request, LocalSettings.default_skin + '/history.html', {'historys': historys, 'title': title, 'page': int(page), 'num_pages': paginator.num_pages})
        
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
            return render(request, LocalSettings.default_skin + '/revert.html', {'error': '해당 문서가 존재하지 않습니다.', 'title': title}, status=404)
            
        try:
            revert_revision = Revision.objects.get(page=page.id, rev=rev)
        except ObjectDoesNotExist:
            return render(request, LocalSettings.default_skin + '/revert.html', {'error': '해당 리비전이 존재하지 않습니다.', 'title': title}, status=404)
            
        pro_revision = Revision.objects.filter(page=page.id).order_by('-id').first()
        new_rev = pro_revision.rev + 1
        increase = len(revert_revision.text) - len(pro_revision.text)
        
        # 사용자
        editor = __get_user(request)
                
        if page.namespace == 2:
            if not request.user.is_active or request.user.username != re.sub('\.(css|js)$', '', title[4:]):
                return render(request, LocalSettings.default_skin + '/revert.html', {'title': title,'text': revert_revision.text, 'rev': rev, 'error': '사용자 문서는 본인만 편집 가능합니다.'})
                
            
        Revision(text=revert_revision.text, page=page, comment='r' + str(revert_revision.rev) + '으로 되돌림: ' + request.POST['comment'], rev=new_rev, increase=increase, user=editor['user'], ip=editor['ip']).save()
        
        revert_parser = NamuMarkParser(revert_revision.text, title)
        pro_parser = NamuMarkParser(pro_revision.text, title)
        
        __insert(revert_parser, pro_parser, page.id, new_rev)
        
        return HttpResponseRedirect(reverse('view', kwargs={'title': title}) + '?alert=successRevert')

        
def random(request):
    my_ids = Page.objects.filter(is_deleted=False, is_created=True, namespace=0).values_list('id', flat=True)
    rand_ids = choice(list(my_ids))
    return redirect('view', title=Page.objects.get(id=rand_ids).title)
    
def rename(request, title=None):
    if request.method == 'GET':
        if title == None:
            return redirect('/')
            
        return render(request, LocalSettings.default_skin + '/rename.html', {'title': title})
        
    elif request.method == 'POST':
        if title == None:
            return redirect('/')
            
        try:
            page = Page.objects.get(title=title)
        except ObjectDoesNotExist:
            return render(request, LocalSettings.default_skin + '/rename.html', {'error': '해당 문서가 존재하지 않습니다.', 'title': title}, status=404)
            
        pro_revision = Revision.objects.filter(page=page.id).order_by('-id').first()
        
        
        editor = __get_user(request)
        
        namespace = __get_namespace(title)
        
        if namespace == 2:
            return render(request, LocalSettings.default_skin + '/rename.html', {'title': title, 'error': '사용자 문서는 이동할 수 없습니다.'})
        
        page.title = request.POST['changedTitle']
        page.namespace = namespace
        page.save()

            
        Revision(text=pro_revision.text, page=page, comment= request.POST['changedTitle'] + '으로 이동: ' + request.POST['comment'], rev=pro_revision.rev + 1, increase=0, user=editor['user'], ip=editor['ip']).save()
        
        return HttpResponseRedirect(reverse('view', kwargs={'title': title}) + '?alert=successRename')
        
def backlink(request, title=None):
    if request.method == 'GET':
        if title == None:
            return redirect('/')
            
        try:
            page = Page.objects.get(title=title)
        except ObjectDoesNotExist:
            return render(request, LocalSettings.default_skin + '/backlink.html', {'error': '해당 문서가 존재하지 않습니다.', 'title': title}, status=404)
        
        if page.backlink == None or page.backlink == "":
            return render(request, LocalSettings.default_skin + '/backlink.html', {'error': '역링크가 존재하지 않습니다.', 'title': title})
            
        backlinks = list(filter(None, page.backlink.split(',')))
        
        paginator = Paginator(backlinks, 20)
        
        if not 'page' in request.GET:
            page_i = 1
        else:
            page_i = request.GET.get('page')
            
        try:
            backlink_ids = paginator.page(page_i)
        except EmptyPage:
            backlink_ids = paginator.page(paginator.num_pages)
            
        backlink_titles = []
        for backlink_id in backlink_ids:
            backlink_titles.append(Page.objects.get(pk=backlink_id).title)
        backlink_titles.sort(key=str.lower)
        
        backlinks = OrderedDict()
        BASE_CODE, CHOSUNG = 44032, 588
        CHOSUNG_LIST = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
        for backlinked_title in backlink_titles:
            if backlinked_title.lower().startswith(tuple(string.ascii_lowercase)):
                try:
                    backlinks[backlinked_title[0].upper()].append(backlinked_title)
                except KeyError:
                    backlinks[backlinked_title[0].upper()] = []
                    backlinks[backlinked_title[0].upper()].append(backlinked_title)
            elif re.match('[ㄱ-ㅎㅏ-ㅣ가-힣]', backlinked_title[0]):
                char_code = ord(backlinked_title[0]) - BASE_CODE
                char1 = int(char_code / CHOSUNG)
                try:
                    backlinks[CHOSUNG_LIST[char1]].append(backlinked_title)
                except KeyError:
                    backlinks[CHOSUNG_LIST[char1]] = []
                    backlinks[CHOSUNG_LIST[char1]].append(backlinked_title)
            else:
                try:
                    backlinks['etc'].append(backlinked_title)
                except KeyError:
                    backlinks['etc'] = []
                    backlinks['etc'].append(backlinked_title)
                
        return render(request, LocalSettings.default_skin + '/backlink.html', {'backlinks': backlinks, 'title': title, 'page': int(page_i), 'num_pages': paginator.num_pages})
        
def delete(request, title=None):
    if request.method == 'GET':
        if title == None:
            return redirect('/')
            
        return render(request, LocalSettings.default_skin + '/delete.html', {'title': title})
        
    elif request.method == 'POST':
        if title == None:
            return redirect('/')
            
        try:
            page = Page.objects.get(title=title)
        except ObjectDoesNotExist:
            return render(request, LocalSettings.default_skin + '/delete.html', {'error': '해당 문서가 존재하지 않습니다.', 'title': title}, status=404)
            
        pro_revision = Revision.objects.filter(page=page.id).order_by('-id').first()
        
        
        editor = __get_user(request)
        
        
        if page.namespace == 2:
            if not request.user.is_active or request.user.username != re.sub('\.(css|js)$', '', title[4:]):
                return render(request, LocalSettings.default_skin + '/delete.html', {'title': title, 'error': '사용자 문서는 본인만 삭제 가능합니다.'})
        
        page.is_deleted = True
        page.save()
            
        Revision(text="", page=page, comment='삭제: ' + request.POST['comment'], rev=pro_revision.rev + 1, increase=-len(pro_revision.text), user=editor['user'], ip=editor['ip']).save()
        
        return HttpResponseRedirect(reverse('view', kwargs={'title': title}) + '?alert=successDelete')
            
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
        
def __save_backlink(each_link, page_id):
    try:
        each_link_page = Page.objects.get(title=each_link)
    except ObjectDoesNotExist:
        namespace = __get_namespace(each_link)
        Page(title=each_link, namespace=namespace, backlink=str(page_id) + ',', is_created=False).save()
    else:
        if each_link_page.backlink == None:
            each_link_page.backlink = str(page_id) + ','
        else:
            each_link_page.backlink += str(page_id) + ','
        each_link_page.save()
        
def __get_user(request):
    if request.user.is_active:
        user = User.objects.get(username=request.user.username)
        ip = None
    else:
        user = None
        ip_address = get_ip(request)
        try:
            ip = Ip.objects.get(ip=ip_address)
        except ObjectDoesNotExist:
            Ip(ip=ip_address).save()
            ip = Ip.objects.get(ip=ip_address)
            
    return {'user': user, 'ip': ip}
    
def __get_namespace(title):
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
    elif title.startswith('사용자:'):
        namespace = 2
    else:
        namespace = 0
        
    return namespace
    
def __insert(now_parser, pro_parser, page_id, rev):
    # 분류
    now_category = set(now_parser.get_category())
    if rev > 1:
        pro_category = set(pro_parser.get_category())
        for each_category in pro_category - now_category:
            each_category_page = Page.objects.get(title=each_category)
            each_category_page.category = each_category_page.category.replace(str(page_id) + ',', '')
            each_category_page.save()
        
        for each_category in now_category - pro_category:
            __save_category(each_category, page_id)
    else:
        for each_category in now_category:
            __save_category(each_category, page_id)
            
    # 역링크
    now_links = set(now_parser.get_link())
    if rev > 1:
        pro_links = set(pro_parser.get_link())
        for each_link in pro_links - now_links:
            each_link_page = Page.objects.get(title=each_link)
            each_link_page.backlink = each_link_page.backlink.replace(str(page_id) + ',', '')
            each_link_page.save()
            
        for each_link in now_links - pro_links:
            __save_backlink(each_link, page_id)
    else:
        for each_link in now_links:
            __save_backlink(each_link, page_id)


        
class signup(CreateView):
    template_name = LocalSettings.default_skin + '/signup.html'
    form_class = UserCreationForm
    success_url = "/?alert=successSignup"
    