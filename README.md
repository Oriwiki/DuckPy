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
LocalSettings.py를 생성 후 다음과 같이 위키 정보를 입력합니다. DB 종류는 django에서 지원하는 것이라면 어떤 것이든 상관없습니다.

```python
#데이터베이스 설정
db = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', #DB 종류
        'NAME': '', # DB명
        'USER': '', # 데이터베이스 계정
        'PASSWORD': '', # 계정 비밀번호
        'HOST': '', # 데이터베이스 주소
        'PORT': '', # 데이터베이스 포트(보통은 3306)
    }
}

#위키 이름
project_name = "DuckWiki"

#메인 페이지 제목
#주의: 메인 페이지 제목은 project_name + mainpage_title로 결정됩니다. 따라서 mainpage_title에 'DuckWiki:FrontPage'라고 입력시 실제로 입력되는 메인 페이지 제목은 'DuckWiki:DuckWiki:FrontPage'가 되어버립니다.
mainpage_title = "FrontPage"

#스킨 설정
default_skin = "default_skin"
```

그리고나서 아래 명령을 입력합니다. 그러면 http://localhost:8000 에 접속할 수 있는 임시 서버를 돌릴 수 있습니다.
```
python manage.py migrate
python manage.py runserver
```


## 기타
버그 레포트는 이슈에 본 github 페이지의 이슈에 등록해주시면 감사하겠습니다.

풀 리퀘스트는 언제나 쌍수 들고 환영합니다!

