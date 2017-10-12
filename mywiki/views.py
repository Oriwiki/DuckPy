from django.shortcuts import render
from django.http import HttpResponse
from NamuMarkParser import NamuMarkParser
from bs4 import BeautifulSoup

# Create your views here.
def index(request):
    input = """
(iii)[* 현존하거나 이미 사라진 문화적 전통이나 문명의 독보적 또는 적어도 특출한 증거일 것], (ⅳ)[* 인류 역사에 있어 중요 단계를 예증하는 건물, 건축이나 기술의 총체, 경관 유형의 대표적 사례일 것], (vi)[* 사건이나 실존하는 전통, 사상이나 신조, 보편적 중요성이 탁월한 예술 및 문학작품과 직접 또는 가시적으로 연관될 것] 거거

본문[* 각주 안의 [* 각주]] 갸갸

[* [[그]]는 전사했다.] 쿠쿠

본문[*A 문자가 다른 각주]
본문[*B 같은 각주를 반복]
본문[*B]
"""

    title = ""
    
    soup = BeautifulSoup(NamuMarkParser().parse(input, title), 'html.parser')
    

    return render(request, 'wiki.html', {'parse': soup.prettify(), 'title': title})

