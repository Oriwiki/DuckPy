# DuckPy

파이썬으로 만든 나무마크 위키 엔진을 개발 중에 있습니다.

아직 개발 초창기이므로 실제 서비스에 적용하지 말아 주십시오.

## 의존
* 파이썬 3
* Django
* pyparsing
* BeautifulSoup

향후 더 추가될 수 있습니다.

## 사용법
아직 Form도 생성하지 않았기 때문에 mywiki/views.py의 input 변수를 수정 후,
```
python manage.py runserver
```
하여 임시로 서버를 돌리시고, http://localhost:8000 으로 접속하시길 바랍니다.

## 기타
버그 레포트는 이슈에 본 github 페이지의 이슈에 등록해주시면 감사하겠습니다.

풀 리퀘스트는 언제나 쌍수 들고 환영합니다!