from django.shortcuts import render
from django.shortcuts import redirect
from django.http import HttpResponse
from NamuMarkParser import NamuMarkParser
from bs4 import BeautifulSoup
from .models import *
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
import LocalSettings

# Create your views here.

def edit(request, title, section=0):
    if request.method == 'GET':
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
        
        if 'preview' in request.POST:
            soup = BeautifulSoup(NamuMarkParser(request.POST['text'], title).parse())
            return render(request, 'edit.html', {'title': title, 'text': request.POST['text'], 'preview': soup.prettify()})
    
        try:
            Page(title=title).save()
        except IntegrityError:
            pass
            
            
        
        Revision(text=request.POST['text'], page=Page.objects.get(title=title), comment=request.POST['comment']).save()
    
        return redirect('/w/' + title)
        
def view(request, title):
    if request.method == 'GET':
        if title == None:
            title = LocalSettings.mainpage_title
            
        try:
            page_id = Page.objects.get(title=title).id
        except ObjectDoesNotExist:
            Page(title=title).save()
            page = Page.objects.get(title=title)
            Revision(text='Hello, World!', page=page, comment='This is testing revision.').save()
            page_id = page.id
            

            
        input = Revision.objects.filter(page=page_id).order_by('-id').first().text
    
        soup = BeautifulSoup(NamuMarkParser(input, title).parse(), 'html.parser')
        return render(request, 'wiki.html', {'parse': soup.prettify(), 'title': title})
        