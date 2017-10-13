from django.shortcuts import render
from django.http import HttpResponse
from NamuMarkParser import NamuMarkParser
from bs4 import BeautifulSoup

# Create your views here.
def index(request):
    input = """
하핫    

[목차]
== test ==
ab
bbbb

== test2 ==
ddd
"""

    title = "test"
    
    soup = BeautifulSoup(NamuMarkParser(input, title).parse(), 'html.parser')
    

    return render(request, 'wiki.html', {'parse': soup.prettify(), 'title': title})

