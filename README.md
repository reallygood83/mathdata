# 학생 설문 분석 MCP (Mathematics Class Profile)

학생들의 수학 수업 관련 설문 데이터를 분석하고 시각화하는 Streamlit 웹 애플리케이션입니다.

## 주요 기능

- 학생별 설문 응답 분석
- 문항별 평균 점수 분석
- 학생별 변화 추이 분석
- 문항별 상관관계 분석
- 분석 결과 이미지 다운로드

## 설치 방법

1. 저장소를 클론합니다:
```bash
git clone https://github.com/yourusername/mathdata.git
cd mathdata
```

2. 가상환경을 생성하고 활성화합니다:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

3. 필요한 패키지를 설치합니다:
```bash
pip install -r requirements.txt
```

## Google API 설정

1. [Google Cloud Console](https://console.cloud.google.com/)에 접속합니다.
2. 새 프로젝트를 생성하거나 기존 프로젝트를 선택합니다.
3. Google Sheets API를 사용 설정합니다.
4. 사용자 인증 정보 > 서비스 계정 > 키 만들기를 선택합니다.
5. JSON 형식의 키를 다운로드합니다.
6. 다운로드한 JSON 파일을 프로젝트 루트 디렉토리에 `credentials.json`으로 저장합니다.

## 실행 방법

```bash
streamlit run app.py
```

## 사용 방법

1. 사이드바에서 Google API 인증 정보를 설정합니다:
   - `credentials.json` 파일을 업로드하거나
   - 환경 변수 `GOOGLE_CREDENTIALS_PATH`에 인증 파일 경로를 설정합니다.

2. 구글 스프레드시트 설정:
   - 스프레드시트 ID를 입력합니다.
   - 데이터 범위를 입력합니다 (예: Sheet1!A1:F100).

3. 분석 설정:
   - 분석 유형을 선택합니다.
   - 학생별 분석인 경우 학생을 선택합니다.

4. '분석 실행' 버튼을 클릭하여 결과를 확인합니다.

## 주의사항

- `credentials.json` 파일은 절대 GitHub에 업로드하지 마세요.
- 스프레드시트는 서비스 계정 이메일과 공유되어야 합니다.
- 설문 데이터는 지정된 형식을 따라야 합니다.

## 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다. 

streamlit==1.29.0
pandas==2.1.3
matplotlib==3.8.2
seaborn==0.13.0
google-api-python-client==2.108.0
google-auth-httplib2==0.1.1
google-auth-oauthlib==1.1.0
python-dotenv==1.0.0 