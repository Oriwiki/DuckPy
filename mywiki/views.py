from django.shortcuts import render
from django.http import HttpResponse
from NamuMarkParser import NamuMarkParser
from bs4 import BeautifulSoup

# Create your views here.
def index(request):
    input = """
<math>1 + 1 = 2</math>
"""

    title = ""
    
    soup = BeautifulSoup(NamuMarkParser().parse(input, title), 'html.parser')
    

    return render(request, 'wiki.html', {'parse': soup.prettify(), 'title': title})

