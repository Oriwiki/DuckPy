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
LocalSettings.py를 생성 후 다음과 같이 DB 정보를 입력합니다. DB 종류는 django에서 지원하는 것이라면 어떤 것이든 상관없습니다.
```
db = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'django_locker', # DB명
        'USER': '', # 데이터베이스 계정
        'PASSWORD': '', # 계정 비밀번호
        'HOST': '', # 데이테베이스 주소(IP)
        'PORT': '', # 데이터베이스 포트(보통은 3306)
    }
}
```

아직 Form도 생성하지 않았기 때문에 mywiki/views.py의 input 변수를 수정 후,
```
python manage.py runserver
```
하여 임시로 서버를 돌리시고, http://localhost:8000 으로 접속하시길 바랍니다.

## 기타
버그 레포트는 이슈에 본 github 페이지의 이슈에 등록해주시면 감사하겠습니다.

풀 리퀘스트는 언제나 쌍수 들고 환영합니다!
