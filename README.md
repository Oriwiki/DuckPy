# DuckPy

파이썬으로 만든 나무마크 위키 엔진을 개발 중에 있습니다.

아직 개발 초창기이므로 실제 서비스에 적용하지 말아 주십시오.

## 의존
* 파이썬 3
* Django
* pyparsing
* BeautifulSoup
* Django REST framework
* Django Debug Toolbar

향후 더 추가될 수 있습니다.

## 사용법

아래 명령을 입력합니다. 그러면 http://localhost:8000 에 접속할 수 있는 임시 서버를 돌릴 수 있습니다.
```
python manage.py makelocalsettings
python manage.py migrate
python manage.py runserver
```


## 기타
버그 레포트는 이슈에 본 github 페이지의 이슈에 등록해주시면 감사하겠습니다.

풀 리퀘스트는 언제나 쌍수 들고 환영합니다!

