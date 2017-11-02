# 쇼트컷
from django.shortcuts import render, get_object_or_404, redirect
# HTTP
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect, Http404
# 예외
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
# 뷰
from django.contrib.auth.forms import UserCreationForm
from django.views.generic.base import TemplateView, RedirectView
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView
from django.views import View
from django.template import RequestContext
# 모델
from django.contrib.auth.models import User
from .models import *
# 기타 도구
from django.core.paginator import Paginator, EmptyPage
from django.core.urlresolvers import reverse
# 기타
from NamuMarkParser import NamuMarkParser
from bs4 import BeautifulSoup
import LocalSettings
import difflib
from urllib.parse   import quote, unquote
import string
from collections import OrderedDict
import re
from random import choice
from ipware.ip import get_ip
import ipaddress
import json


## 위키 ##

# 문서 보기
class WikiView(TemplateView):
    template_name = LocalSettings.default_skin + '/wiki.html'
    redirect = False
    def get(self, request, *args, **kwargs):
        get = super(WikiView, self).get(request, *args, **kwargs)
        if self.redirect:
            return HttpResponseRedirect(reverse('view', kwargs={'title': self.redirect}) + '?redirectFrom=' + quote(self.kwargs['title']))
        return get        
    
    def get_context_data(self, **kwargs):
        context = super(WikiView, self).get_context_data(**kwargs)
        try:
            page = Page.objects.get(title=self.kwargs['title'], is_deleted=False)
        except ObjectDoesNotExist:
            raise Http404(json.dumps({'type': 'WikiPageNotFound', 'template_name': 'wiki.html', 'title': self.kwargs['title']}))
            
        if 'rev' in self.request.GET:
            rev = self.request.GET['rev']
        else:
            rev = 0
            
        if page.namespace == 4:
            categories = self.__category(self.request, page, rev)
            context['categories'] = categories['categories']
            context['page'] = categories['page']
            context['num_pages'] = categories['num_pages']
            
        if page.is_created == False:
            if page.namespace == 4:
                raise Http404(json.dumps({'type': 'WikiPageNotFound', 'template_name': 'wiki.html', 'title': self.kwargs['title'], 'categories': categories}))
            else:
                raise Http404(json.dumps({'type': 'WikiPageNotFound', 'template_name': 'wiki.html', 'title': self.kwargs['title']}))
        
        if rev == 0:
            revision = Revision.objects.filter(page=page.id).order_by('-id').first()
        else:
            try:
                revision = Revision.objects.get(page=page, rev=rev)
            except ObjectDoesNotExist:
                raise Http404(json.dumps({'type': 'WikiPageNotFound', 'template_name': 'wiki.html', 'title': self.kwargs['title']}))
            
        if revision.text.startswith(('#redirect ', '#넘겨주기 ')):
            context['parse'] = revision.text
            if rev == 0:
                if ('redirect' in self.request.GET and int(self.request.GET['redirect']) == 1) or not 'redirect' in self.request.GET:
                    if revision.text.startswith('#redirect '):
                        self.redirect = revision.text[10:]
                    else:
                        self.redirect = revision.text[6:]
        else:
            soup = BeautifulSoup(NamuMarkParser(revision.text, self.kwargs['title']).parse(), 'html.parser')
            context['parse'] = soup.prettify()
        
        return context
        
    def __category(self, request, page, rev):
        BASE_CODE, CHOSUNG = 44032, 588
        CHOSUNG_LIST = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
        
        if page.category == None or page.category == "":
            return render(request, LocalSettings.default_skin + '/wiki.html', {'error': '분류가 존재하지 않습니다.', 'title': self.kwargs['title']})
            
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
                        
        return {'categories': categories, 'page': int(page_i), 'num_pages': paginator.num_pages}
                  
# 문서 편집
class EditView(TemplateView):
    template_name = LocalSettings.default_skin + '/edit.html'
    
    def get_context_data(self, **kwargs):
        context = super(EditView, self).get_context_data(**kwargs)
        
        if 'section' in self.request.GET:
            context['section'] = int(self.request.GET['section'])
        else:
            context['section'] = 0
        
        try:
            page = Page.objects.get(title=self.kwargs['title'])
        except ObjectDoesNotExist:
            context['text'] = ""
            context['section'] = 0
            return context
        else:
            if page.is_created == True:
                context['text'] = Revision.objects.filter(page=page).order_by('-id').first().text
            else:
                context['text'] = ""
                
        if context['section'] > 0 and context['text'] != "":
            toc = NamuMarkParser(text, self.kwargs['title']).get_toc()
            try:
                context['text'] = toc[section - 1][3]
            except IndexError:
                context['section'] = 0
                
        return context    
        
    def post(self, request, *args, **kwargs):
        # 미리보기
        if 'preview' in request.POST:
            soup = BeautifulSoup(NamuMarkParser(request.POST['text'], self.kwargs['title']).parse(), "html.parser")
            return render(request, LocalSettings.default_skin + '/edit.html', {'title': self.kwargs['title'],'text': request.POST['text'], 'preview': soup.prettify(), 'section': request.POST['section']})
        
        # 저장
        namespace = get_namespace(self.kwargs['title'])
        
        if namespace == 2:
            if not request.user.is_active or request.user.username != re.sub('\.(css|js)$', '', title[4:]):
                return render(request, LocalSettings.default_skin + '/edit.html', {'title': self.kwargs['title'],'text': request.POST['text'], 'section': request.POST['section'], 'error': '사용자 문서는 본인만 편집 가능합니다.'})
                
        # 사용자
        editor = get_user(request)
        
        text = request.POST['text']
        
        if 'section' in request.POST:
            section = int(request.POST['section'])
        else:
            section = 0
        
        try:
            Page(title=self.kwargs['title'], namespace=namespace, is_created=True).save()
        except IntegrityError:
            page = Page.objects.get(title=self.kwargs['title'])
            if page.is_created == True:
                pro_revision = Revision.objects.filter(page=page).order_by('-id').first()
                pro_parser = NamuMarkParser(pro_revision.text, self.kwargs['title'])
                
                # 단락 편집
                if section > 0:
                    text = self.__section(request, pro_parser, section)
                
                rev = pro_revision.rev + 1
                increase = len(text) - len(pro_revision.text)
            else:
                rev = 1
                increase = len(text)
                pro_parser = None
                page.is_created = True
                
            if page.is_deleted == True:
                page.is_deleted = False
                
            page.save()
        else:
            page = Page.objects.get(title=self.kwargs['title'])
            pro_parser = None
            rev = 1
            increase = len(text)
            
        Revision(text=text, page=page, comment=request.POST['comment'], rev=rev, increase=increase, user=editor['user'], ip=editor['ip']).save()
        
        now_parser = NamuMarkParser(text, self.kwargs['title'])
        
        insert(now_parser, pro_parser, page.id, rev)
        
        return HttpResponseRedirect(reverse('view', kwargs={'title': self.kwargs['title']}) + '?alert=successEdit')
            
    def __section(request, pro_parser, section):
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
        return text
        
# 문서 RAW 보기
class RawView(View):
    def get(self, request, *args, **kwargs):
        try:
            page = Page.objects.get(title=self.kwargs['title'])
        except ObjectDoesNotExist:
            return HttpResponseNotFound()
            
        if 'rev' in request.GET:
            rev = request.GET['rev']
        else:
            rev = 0
            
        if rev == 0:
            return HttpResponse(Revision.objects.filter(page=page).order_by('-id').first().text, content_type='text/plain; charset="utf-8"')
        else:
            try:
                return HttpResponse(Revision.objects.get(page=page, rev=rev).text, content_type='text/plain; charset="utf-8"')
            except ObjectDoesNotExist:
                return HttpResponseNotFound()

# 문서 diff
class DiffView(TemplateView):
    template_name = LocalSettings.default_skin + '/diff.html'

    def get_context_data(self, **kwargs):
        context = super(DiffView, self).get_context_data(**kwargs)
        try:
            page = Page.objects.get(title=self.kwargs['title'], is_deleted=False, is_created=True)
        except ObjectDoesNotExist:
            raise Http404(json.dumps({'type': 'WikiPageNotFound', 'template_name': 'diff.html', 'title': self.kwargs['title']}))
            
        if not 'rev' in self.request.GET or not 'oldrev' in self.request.GET:
            raise Http404(json.dumps({'type': 'WikiRevisionNotFound', 'template_name': 'diff.html', 'title': self.kwargs['title']}))

        rev = self.request.GET['rev']
        oldrev = self.request.GET['oldrev']
        
        if rev == oldrev:
            context['error'] = '비교하려는 리비전이 같습니다.'
            return context
            
        try:
            text = Revision.objects.get(page=page, rev=rev).text
            oldtext = Revision.objects.get(page=page, rev=oldrev).text
        except ObjectDoesNotExist:
            raise Http404(json.dumps({'type': 'WikiRevisionNotFound', 'template_name': 'diff.html', 'title': self.kwargs['title']}))
            
        if text == oldtext:
            context['diff'] = '동일합니다.'
            return context
            
        if text == "" or oldtext == "":
            context['diff'] = '비교하려는 리비전에 글이 없습니다.'
            return context
            
        context['diff'] = difflib.HtmlDiff().make_table(oldtext.splitlines(True), text.splitlines(True),  context=True).replace(' nowrap="nowrap"', '')
        
        return context
            
# 문서 역사
class HistoryView(ListView):
    template_name = LocalSettings.default_skin + '/history.html'
    context_object_name = 'historys'
    paginate_by = 20
    
    def get_queryset(self):
        try:
            page = Page.objects.get(title=self.kwargs['title'])
        except ObjectDoesNotExist:
            raise Http404(json.dumps({'type': 'WikiPageNotFound', 'template_name': 'history.html', 'title': self.kwargs['title']}))
        return Revision.objects.filter(page=page).order_by('-id').all()

# 문서 되돌리기
class RevertView(TemplateView):
    template_name = LocalSettings.default_skin + '/revert.html'
            
    def get_context_data(self, **kwargs):
        context = super(RevertView, self).get_context_data(**kwargs)
        
        if not 'rev' in self.request.GET:
            raise Http404(json.dumps({'type': 'WikiRevisionNotFound', 'template_name': 'revert.html', 'title': self.kwargs['title']}))
            
        rev = self.request.GET['rev']       
            
        try:
            page = Page.objects.get(title=self.kwargs['title'])
        except ObjectDoesNotExist:
            raise Http404(json.dumps({'type': 'WikiPageNotFound', 'template_name': 'revert.html', 'title': self.kwargs['title']}))
            
        try:
            revision = Revision.objects.get(page=page, rev=rev)
        except ObjectDoesNotExist:
            raise Http404(json.dumps({'type': 'WikiRevisionNotFound', 'template_name': 'revert.html', 'title': self.kwargs['title']}))
            
        context['text'] = revision.text
        context['rev'] = rev
        return context
        
    def post(self, request, *args, **kwargs):
        if not 'rev' in self.request.POST:
            return render(self.request, LocalSettings.default_skin + '/revert.html', {'error': '되돌리려는 리비전이 제시되지 않았습니다.', 'title': self.kwargs['title']}, status=412)
            
        rev = self.request.POST['rev']
        
        try:
            page = Page.objects.get(title=self.kwargs['title'])
        except ObjectDoesNotExist:
            return render(self.request, LocalSettings.default_skin + '/revert.html', {'error': '해당 문서가 존재하지 않습니다.', 'title': self.kwargs['title']}, status=404)
            
        try:
            revert_revision = Revision.objects.get(page=page, rev=rev)
        except ObjectDoesNotExist:
            return render(self.request, LocalSettings.default_skin + '/revert.html', {'error': '해당 리비전이 존재하지 않습니다.', 'title': self.kwargs['title']}, status=404)
            
        pro_revision = Revision.objects.filter(page=page).order_by('-id').first()
        new_rev = pro_revision.rev + 1
        increase = len(revert_revision.text) - len(pro_revision.text)
        
        # 사용자
        editor = get_user(self.request)
        
        if page.namespace == 2:
            if not self.request.user.is_active or self.request.user.username != re.sub('\.(css|js)$', '', self.kwargs['title'][4:]):
                return render(request, LocalSettings.default_skin + '/revert.html', {'title': self.kwargs['title'],'text': revert_revision.text, 'rev': rev, 'error': '사용자 문서는 본인만 편집 가능합니다.'})
                
        Revision(text=revert_revision.text, page=page, comment='r' + str(revert_revision.rev) + '으로 되돌림: ' + self.request.POST['comment'], rev=new_rev, increase=increase, user=editor['user'], ip=editor['ip']).save()
        
        revert_parser = NamuMarkParser(revert_revision.text, self.kwargs['title'])
        pro_parser = NamuMarkParser(pro_revision.text, self.kwargs['title'])
        
        insert(revert_parser, pro_parser, page.id, new_rev)
        
        return HttpResponseRedirect(reverse('view', kwargs={'title': self.kwargs['title']}) + '?alert=successRevert')
        
# 랜덤
def random(request):
    my_ids = Page.objects.filter(is_deleted=False, is_created=True, namespace=0).values_list('id', flat=True)
    rand_ids = choice(list(my_ids))
    return redirect('view', title=Page.objects.get(id=rand_ids).title)
 
# 문서 이동
class RenameView(UpdateView):
    fields = ['title']
    template_name = LocalSettings.default_skin + '/rename.html'
    
    def get_object(self):
        try:
            return Page.objects.get(title=self.kwargs['title'], is_created=True)
        except ObjectDoesNotExist:
            raise Http404(json.dumps({'type': 'WikiPageNotFound', 'template_name': 'rename.html', 'title': self.kwargs['title']}))
    
    def form_valid(self, form):
        namespace = get_namespace(self.request.POST['title'])
        if self.object.namespace == 2 or namespace == 2:
            return render(request, LocalSettings.default_skin + '/rename.html', {'title': title, 'error': '사용자 문서는 이동할 수 없습니다.'})
        pro_revision = Revision.objects.filter(page=self.object).order_by('-id').first()
        editor = get_user(self.request)
        self.object.namespace = namespace
        
        Revision(text=pro_revision.text, page=self.object, comment= self.request.POST['title'] + '으로 이동: ' + self.request.POST['comment'], rev=pro_revision.rev + 1, increase=0, user=editor['user'], ip=editor['ip']).save()
        
        return super(RenameView, self).form_valid(form)
        
    def get_success_url(self):
        return reverse('view', kwargs={'title': self.request.POST['title']}) + '?alert=successRename'
    
# 역링크
class BacklinkView(TemplateView):
    template_name = LocalSettings.default_skin + '/backlink.html'
    
    def get_context_data(self, **kwargs):
        context = super(BacklinkView, self).get_context_data(**kwargs)
    
        try:
            page = Page.objects.get(title=self.kwargs['title'])
        except ObjectDoesNotExist:
            raise Http404(json.dumps({'type': 'WikiPageNotFound', 'template_name': 'backlink.html', 'title': self.kwargs['title']}))
            
        if page.backlink == None or page.backlink == "":
            raise Http404(json.dumps({'type': 'BacklinkNotFound', 'template_name': 'backlink.html', 'title': self.kwargs['title']}))
            
        backlinks = list(filter(None, page.backlink.split(',')))
        
        paginator = Paginator(backlinks, 20)
        
        if not 'page' in self.request.GET:
            context['page'] = 1
        else:
            context['page'] = self.request.GET.get('page')
            
        try:
            backlink_ids = paginator.page(context['page'])
        except EmptyPage:
            backlink_ids = paginator.page(paginator.num_pages)

        backlink_titles = []
        for backlink_id in backlink_ids:
            backlink_titles.append(Page.objects.get(pk=backlink_id).title)
        backlink_titles.sort(key=str.lower)
        
        context['backlinks'] = OrderedDict()
        BASE_CODE, CHOSUNG = 44032, 588
        CHOSUNG_LIST = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
        for backlinked_title in backlink_titles:
            if backlinked_title.lower().startswith(tuple(string.ascii_lowercase)):
                try:
                    context['backlinks'][backlinked_title[0].upper()].append(backlinked_title)
                except KeyError:
                    context['backlinks'][backlinked_title[0].upper()] = []
                    context['backlinks'][backlinked_title[0].upper()].append(backlinked_title)
            elif re.match('[ㄱ-ㅎㅏ-ㅣ가-힣]', backlinked_title[0]):
                char_code = ord(backlinked_title[0]) - BASE_CODE
                char1 = int(char_code / CHOSUNG)
                try:
                    context['backlinks'][CHOSUNG_LIST[char1]].append(backlinked_title)
                except KeyError:
                    context['backlinks'][CHOSUNG_LIST[char1]] = []
                    context['backlinks'][CHOSUNG_LIST[char1]].append(backlinked_title)
            else:
                try:
                    context['backlinks']['etc'].append(backlinked_title)
                except KeyError:
                    context['backlinks']['etc'] = []
                    context['backlinks']['etc'].append(backlinked_title)
                    
        context['num_pages'] = paginator.num_pages
        
        return context
    
# 문서 삭제
class DeleteView(UpdateView):
    fields = ['is_deleted']
    template_name = LocalSettings.default_skin + '/delete.html'

    def get_object(self):
        try:
            return Page.objects.get(title=self.kwargs['title'], is_created=True, is_deleted=False)
        except ObjectDoesNotExist:
            raise Http404(json.dumps({'type': 'WikiPageNotFound', 'template_name': 'delete.html', 'title': self.kwargs['title']}))

    def form_valid(self, form):
        if self.object.namespace == 2:
            return render(request, LocalSettings.default_skin + '/rename.html', {'title': title, 'error': '사용자 문서는 삭제할 수 없습니다.'})
        pro_revision = Revision.objects.filter(page=self.object).order_by('-id').first()
        editor = get_user(self.request)
        
        Revision(text="", page=self.object, comment= '삭제: ' + self.request.POST['comment'], rev=pro_revision.rev + 1, increase=-len(pro_revision.text), user=editor['user'], ip=editor['ip']).save()
        
        return super(DeleteView, self).form_valid(form)
        
    def get_success_url(self):
        return reverse('view', kwargs={'title': self.request.POST['title']}) + '?alert=successDelete'
 
        
class RecentChangesView(ListView):
    template_name = LocalSettings.default_skin + '/recentchanges.html'
    context_object_name = 'changes'
    paginate_by = 20
    
    def get_queryset(self):
        return Revision.objects.order_by('-id').all()

 
# 404 페이지
def page_not_found(request, exception):
    try:
        exception = json.loads(str(exception))
    except json.decoder.JSONDecodeError:
        return render(request, LocalSettings.default_skin + '/404.html', {}, status=404)
    else:
        if 'type' in exception:
            if exception['type'] == "WikiPageNotFound":
                if 'categories' in exception:
                    return render(request, LocalSettings.default_skin + '/' + exception['template_name'], {'error': '해당 문서가 존재하지 않습니다.', 'title': exception['title'], 'categories': exception['categories']['categories'], 'page': exception['categories']['page'], 'num_pages': exception['categories']['num_pages']}, status=404)
                else:
                    return render(request, LocalSettings.default_skin + '/' + exception['template_name'], {'error': '해당 문서가 존재하지 않습니다.', 'title': exception['title']}, status=404)
            elif exception['type'] == "WikiRevisionNotFound":
                return render(request, LocalSettings.default_skin + '/' + exception['template_name'], {'error': '해당 리비전이 존재하지 않습니다.', 'title': exception['title']}, status=404)
            elif exception['type'] == "ErrorUserPage":
                return render(request, LocalSettings.default_skin + '/' + exception['template_name'], {'error': '사용자 문서는 본인만 편집 가능합니다.', 'title': exception['title']})
            elif exception['type'] == "BacklinkNotFound":
                return render(request, LocalSettings.default_skin + '/' + exception['template_name'], {'error': '역링크가 존재하지 않습니다.', 'title': exception['title']})
            elif exception['type'] == "ContributionNotFound":
                return render(request, LocalSettings.default_skin + '/' + exception['template_name'], {'error': '기여가 존재하지 않습니다.', 'editor': exception['editor']})
        

## 회원 ##

# 회원가입
class signup(CreateView):
    template_name = LocalSettings.default_skin + '/signup.html'
    form_class = UserCreationForm
    success_url = "/?alert=successSignup"

# 기여 
class ContributionView(ListView):
    template_name = LocalSettings.default_skin + '/contribution.html'
    context_object_name = 'contributions'
    paginate_by = 20
    
    def get_queryset(self):
        try:
            ipaddress.ip_address(self.kwargs['editor'])
        except ValueError:
            # 회원
            try:
                editor = User.objects.get(username=self.kwargs['editor'])
                return Revision.objects.filter(user_id=editor).order_by('-id').all()
            except User.DoesNotExist:
                raise Http404(json.dumps({'type': 'UserNotFound', 'template_name': 'contribution.html', 'editor': self.kwargs['editor']}))
            except Revision.DoesNotExist:
                raise Http404(json.dumps({'type': 'ContributionNotFound', 'template_name': 'contribution.html', 'editor': self.kwargs['editor']}))
        else:
            # IP 사용자
            try:
                editor = Ip.objects.get(ip=self.kwargs['editor'])
                return Revision.objects.filter(ip=editor).order_by('-id').all()
            except Ip.DoesNotExist:
                raise Http404(json.dumps({'type': 'UserNotFound', 'template_name': 'contribution.html', 'editor': self.kwargs['editor']}))
            except Revision.DoesNotExist:
                raise Http404(json.dumps({'type': 'ContributionNotFound', 'template_name': 'contribution.html', 'editor': self.kwargs['editor']}))
    
        
## 공통 함수 ##
def get_namespace(title):
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

def get_user(request):
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

def insert(now_parser, pro_parser, page_id, rev):
    # 분류
    now_category = set(now_parser.get_category())
    if rev > 1:
        pro_category = set(pro_parser.get_category())
        for each_category in pro_category - now_category:
            each_category_page = Page.objects.get(title=each_category)
            each_category_page.category = each_category_page.category.replace(str(page_id) + ',', '')
            each_category_page.save()
        
        for each_category in now_category - pro_category:
            save_category(each_category, page_id)
    else:
        for each_category in now_category:
            save_category(each_category, page_id)
            
    # 역링크
    now_links = set(now_parser.get_link())
    if rev > 1:
        pro_links = set(pro_parser.get_link())
        for each_link in pro_links - now_links:
            each_link_page = Page.objects.get(title=each_link)
            each_link_page.backlink = each_link_page.backlink.replace(str(page_id) + ',', '')
            each_link_page.save()
            
        for each_link in now_links - pro_links:
            save_backlink(each_link, page_id)
    else:
        for each_link in now_links:
            save_backlink(each_link, page_id)
            
def save_backlink(each_link, page_id):
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

def save_category(each_category, page_id):
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
        