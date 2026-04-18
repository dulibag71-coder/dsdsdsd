import sys
import os

# 현재 상위 디렉토리(backend) 모듈들을 import할 수 있게 패스 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# main 모듈에서 FastAPI 앱 인스턴스를 가져옵니다.
from main import app
