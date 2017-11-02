from django.core.management.base import BaseCommand, CommandError
from mywiki.models import *
import os
import string
import random
import getpass

class Command(BaseCommand):
    help = 'LocalSettings.py 파일을 간편하게 만들어줍니다.'
    
    def handle(self, *args, **options):
        if os.path.isfile('LocalSettings.py'):
            raise CommandError('이미 LocalSettings.py 파일이 존재합니다.')
    
        lines = []
        lines.append('import os')
        lines.append('')
        lines.append('db = {')
        lines.append("    'default': {")
        
        while True:
            db_engine = int(input("데이터베이스 엔진이 무엇입니까?\n1. MySQL 2. SQLite, 3. PostgreSQL, 4. Oracle\n"))
            if 1 <= db_engine <= 4:
                break
        
        if db_engine == 1:
            lines.append("        'ENGINE': 'django.db.backends.mysql',")
        elif db_engine == 2:
            lines.append("        'ENGINE': 'django.db.backends.sqlite3',")
        elif db_engine == 3:
            lines.append("        'ENGINE': 'django.db.backends.postgresql',")
        elif db_engine == 4:
            lines.append("        'ENGINE': 'django.db.backends.oracle',")
            
        if db_engine == 2:
            db_name = input("SQLite 파일 이름을 입력하시오. (기본값: db.sqlite3): ")
            if not db_name:
                db_name = 'db.sqlite3'
            lines.append("        'NAME': os.path.join(BASE_DIR, '%s')," % db_name)
        else:
            while True:
                db_name = input("데이터베이스 이름을 입력하시오.: ")
                if db_name:
                    break
            
            while True:
                db_user = input("데이터베이스 사용자 이름을 입력하시오.: ")
                if db_user:
                    break
                    
            while True:
                db_password = getpass.getpass("데이터베이스 사용자 비밀번호를 입력하시오.: ")
                if db_password:
                    break
                    
            db_host = input("데이터베이스 서버 주소를 입력하시오.: ")
            db_port = input("데이터베이스 서버 포트를 입력하시오.: ")
            
            lines.append("        'NAME': '%s'," % db_name)
            lines.append("        'USER': '%s'," % db_user)
            lines.append("        'PASSWORD': '%s'," % db_password)
            lines.append("        'HOST': '%s'," % db_host)
            lines.append("        'PORT': '%s'," % db_port)
            
        lines.append("    }")
        lines.append("}")
        lines.append("")
        
        mainpage = input("메인 페이지 제목을 입력하시오. (기본값: FrontPage): ")
        if not mainpage:
            mainpage = 'FrontPage'
        lines.append('mainpage_title = "%s"' % mainpage)
        lines.append('')
        
        while True:
            project_name = input("위키 프로젝트 이름을 입력하시오.: ")
            if project_name:
                break
        lines.append('project_name = "%s"' % project_name)
        lines.append('')
        
        lines.append('default_skin = "default_skin"')
        lines.append('')
        
        chars = ''.join([string.ascii_letters, string.digits, string.punctuation]).replace('\'', '').replace('"', '').replace('\\', '')
        SECRET_KEY = ''.join([random.SystemRandom().choice(chars) for i in range(50)])
        lines.append('SECRET_KEY = "%s"' %  SECRET_KEY)
        
            
        f = open('LocalSettings.py', 'w')
        f.write("\n".join(lines))
        f.close()
        self.stdout.write(self.style.SUCCESS("생성되었습니다."))
