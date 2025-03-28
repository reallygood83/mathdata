# 학생 리포트 시각화 시스템

이 프로젝트는 구글 스프레드시트의 학생 데이터를 가져와서 시각화된 리포트를 생성하는 웹 애플리케이션입니다.

## 설치 방법

1. 필요한 패키지 설치:
```bash
pip install -r requirements.txt
```

2. Google Cloud Console에서 프로젝트를 생성하고 Google Sheets API를 활성화합니다.

3. OAuth 2.0 클라이언트 ID를 생성하고 credentials.json 파일을 다운로드하여 프로젝트 루트 디렉토리에 저장합니다.

## 사용 방법

1. 애플리케이션 실행:
```bash
python -m streamlit run app.py
```

2. 웹 브라우저에서 열리는 인터페이스에서:
   - 구글 스프레드시트 ID 입력
   - 데이터 범위 입력 (예: Sheet1!A1:F100)
   - "데이터 가져오기" 버튼 클릭

3. 데이터가 성공적으로 로드되면 자동으로 시각화된 리포트가 생성됩니다.

## 스프레드시트 형식

스프레드시트는 다음과 같은 열을 포함해야 합니다:
- 학생 이름
- 학번
- 국어
- 수학
- 영어
- 과학
- 사회
- 성적 (총점)

## 주의사항

- 처음 실행 시 Google 계정 인증이 필요합니다.
- credentials.json 파일이 프로젝트 루트 디렉토리에 있어야 합니다.
- 스프레드시트에 대한 읽기 권한이 필요합니다. 

CREDENTIALS_PATH = "실제 credentials 파일의 경로" 

streamlit==1.29.0
pandas==2.1.3
matplotlib==3.8.2
seaborn==0.13.0
google-api-python-client==2.108.0
google-auth-httplib2==0.1.1
google-auth-oauthlib==1.1.0
python-dotenv==1.0.0 