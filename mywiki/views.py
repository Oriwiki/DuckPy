from django.shortcuts import render
from django.http import HttpResponse
from NamuMarkParser import NamuMarkParser
from bs4 import BeautifulSoup

# Create your views here.
def index(request):
    input = """
||<table align=right><-3><#000><:> [[유네스코|{{{#fff '''유네스코'''}}}]] [[세계유산|{{{#fff '''세계유산'''}}}]] ||

"""

    title = ""
    
    soup = BeautifulSoup(NamuMarkParser().parse(input, title), 'html.parser')
    

    return render(request, 'wiki.html', {'parse': soup.prettify(), 'title': title})

