from django.shortcuts import render
from django.http import HttpResponse
from NamuMarkParser import NamuMarkParser
from bs4 import BeautifulSoup

# Create your views here.
def index(request):
    input = """
== test ==
ab

== test2 ==
ddd
"""

    title = ""
    
    soup = BeautifulSoup(NamuMarkParser(input, title).parse(), 'html.parser')
    

    return render(request, 'wiki.html', {'parse': soup.prettify(), 'title': title})

