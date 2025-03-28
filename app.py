import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os.path
import numpy as np
import base64
from io import BytesIO
import json

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'  # 윈도우의 경우
plt.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 깨짐 방지

# Google Sheets API 설정
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

def get_google_sheets_service():
    """구글 스프레드시트 서비스 객체를 생성합니다."""
    try:
        # Streamlit Cloud 환경에서 실행 중인 경우
        if 'GOOGLE_CREDENTIALS' in st.secrets:
            credentials_json = st.secrets['GOOGLE_CREDENTIALS']
            st.success("Streamlit Cloud 환경에서 인증 정보를 성공적으로 로드했습니다.")
        else:
            # 로컬 환경에서 실행 중인 경우
            credentials_path = os.getenv('GOOGLE_CREDENTIALS_PATH')
            
            # 직접 경로 지정 (개발 환경용)
            if not credentials_path:
                # 기본 경로 시도 (현재 디렉토리에 credentials.json 파일이 있는지 확인)
                if os.path.exists('credentials.json'):
                    credentials_path = 'credentials.json'
                    st.info("현재 디렉토리의 credentials.json 파일을 사용합니다.")
                else:
                    st.error("GOOGLE_CREDENTIALS_PATH 환경 변수가 설정되지 않았습니다.")
                    st.info("다음 방법 중 하나로 Google API 인증 정보를 설정해주세요:")
                    st.info("1. 환경 변수 GOOGLE_CREDENTIALS_PATH에 인증 파일 경로 설정")
                    st.info("2. 프로젝트 루트 디렉토리에 credentials.json 파일 위치시키기")
                    st.info("3. Streamlit Cloud를 사용하는 경우 st.secrets에 GOOGLE_CREDENTIALS 설정")
                    return None
            
            with open(credentials_path, 'r') as f:
                credentials_json = f.read()
            st.success(f"{credentials_path}에서 인증 정보를 성공적으로 로드했습니다.")
        
        credentials = service_account.Credentials.from_service_account_info(
            json.loads(credentials_json), scopes=SCOPES)
        service = build('sheets', 'v4', credentials=credentials)
        return service
    except FileNotFoundError:
        st.error(f"인증 파일을 찾을 수 없습니다. 경로를 확인해주세요: {credentials_path}")
        return None
    except json.JSONDecodeError:
        st.error("인증 파일이 올바른 JSON 형식이 아닙니다.")
        return None
    except Exception as e:
        st.error(f"구글 스프레드시트 서비스 생성 중 오류가 발생했습니다: {str(e)}")
        return None

def get_sheet_data(service, spreadsheet_id, range_name):
    """구글 스프레드시트에서 데이터를 가져옵니다."""
    try:
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
        values = result.get('values', [])
        
        if not values:
            st.warning("데이터가 없습니다.")
            return None
        
        df = pd.DataFrame(values[1:], columns=values[0])
        
        # 설문 문항 컬럼명 정리
        survey_columns = {
            '📌 학생 번호를 선택하세요.': '학번',
            '🧑‍🎓 학생 이름을 입력하세요.': '학생 이름',
            '🤩 오늘 수학 수업이 기대돼요. (1점: 전혀 기대되지 않아요 ~ 5점: 매우 기대돼요)': '수업 기대도',
            '😨 오늘 수학 수업이 좀 긴장돼요. (1점: 전혀 긴장되지 않아요 ~ 5점: 매우 긴장돼요)': '긴장도',
            '🎲 오늘 배우는 수학 내용이 재미있을 것 같아요. (1점: 전혀 재미없을 것 같아요 ~ 5점: 매우 재미있을 것 같아요)': '재미 예상도',
            '💪 오늘 수업을 잘 해낼 자신이 있어요. (1점: 전혀 자신 없어요 ~ 5점: 매우 자신 있어요)': '자신감',
            '🎯 지금 수업에 집중하고 있어요. (1점: 전혀 집중하지 못해요 ~ 5점: 완전히 집중하고 있어요)': '집중도',
            '😆 지금 수업이 즐거워요. (1점: 전혀 즐겁지 않아요 ~ 5점: 매우 즐거워요)': '즐거움',
            '🌟 이제 수학 공부에 자신감이 더 생겼어요. (1점: 전혀 그렇지 않아요 ~ 5점: 매우 그래요)': '자신감 변화',
            '🎉 수업 후에 수학이 전보다 더 재미있어졌어요. (1점: 전혀 그렇지 않아요 ~ 5점: 매우 그래요)': '재미 변화',
            '😌 수업 후에는 수학 시간에 전보다 덜 긴장돼요. (1점: 전혀 그렇지 않아요 ~ 5점: 매우 그래요)': '긴장도 변화',
            '🧠 오늘 수업 내용을 잘 이해했어요. (1점: 전혀 이해하지 못했어요 ~ 5점: 매우 잘 이해했어요)': '이해도',
            '📋 ✏️ 오늘 배운 수학 내용을 한 줄로 요약해 보세요.': '수업 요약',
            '📋 💭 오늘 수업에서 스스로 잘한 점이나 아쉬운 점을 한 문장으로 적어 보세요.': '자기 평가'
        }
        
        df = df.rename(columns=survey_columns)
        
        # 숫자형 데이터 변환
        numeric_columns = ['수업 기대도', '긴장도', '재미 예상도', '자신감', '집중도', 
                          '즐거움', '자신감 변화', '재미 변화', '긴장도 변화', '이해도']
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"데이터를 가져오는 중 오류가 발생했습니다: {str(e)}")
        return None

def create_visualization(df, chart_type, student_name=None):
    """지정된 차트 유형에 따라 시각화를 생성하고 base64로 인코딩된 이미지를 반환합니다."""
    if df is None:
        return None, "데이터를 찾을 수 없습니다."
    
    # 그래프 초기화
    plt.clf()
    
    if chart_type == '학생별 설문 응답':
        if student_name is None:
            return None, "학생 이름을 지정해주세요."
        
        student_data = df[df['학생 이름'] == student_name]
        if student_data.empty:
            return None, f"'{student_name}' 학생을 찾을 수 없습니다."
        
        fig, ax = plt.subplots(figsize=(12, 6))
        survey_items = ['수업 기대도', '긴장도', '재미 예상도', '자신감', '집중도', 
                       '즐거움', '자신감 변화', '재미 변화', '긴장도 변화', '이해도']
        values = student_data[survey_items].iloc[0]
        
        plt.bar(survey_items, values)
        plt.title(f'{student_name} 학생의 설문 응답')
        plt.xticks(rotation=45, ha='right')
        plt.ylabel('점수 (1-5)')
        plt.ylim(0, 5)
        
        # 자기 평가 정보 추가
        evaluation_text = f"\n수업 요약: {student_data['수업 요약'].iloc[0]}\n"
        evaluation_text += f"자기 평가: {student_data['자기 평가'].iloc[0]}"
        plt.figtext(0.02, 0.02, evaluation_text, fontsize=8, wrap=True)
    
    elif chart_type == '문항별 평균 점수':
        fig, ax = plt.subplots(figsize=(12, 6))
        survey_items = ['수업 기대도', '긴장도', '재미 예상도', '자신감', '집중도', 
                       '즐거움', '자신감 변화', '재미 변화', '긴장도 변화', '이해도']
        
        means = df[survey_items].mean()
        stds = df[survey_items].std()
        
        plt.bar(survey_items, means, yerr=stds, capsize=5)
        plt.title('문항별 평균 점수 (오차 막대: 표준편차)')
        plt.xticks(rotation=45, ha='right')
        plt.ylabel('평균 점수 (1-5)')
        plt.ylim(0, 5)
        
        # 통계 정보 추가
        stats_text = "통계 정보:\n"
        stats = df[survey_items].describe()
        stats_text += stats.to_string()
        plt.figtext(0.02, 0.02, stats_text, fontsize=8, wrap=True)
    
    elif chart_type == '학생별 변화 추이':
        if student_name is None:
            return None, "학생 이름을 지정해주세요."
        
        student_data = df[df['학생 이름'] == student_name]
        if student_data.empty:
            return None, f"'{student_name}' 학생을 찾을 수 없습니다."
        
        fig, ax = plt.subplots(figsize=(10, 6))
        changes = ['자신감 변화', '재미 변화', '긴장도 변화']
        values = student_data[changes].iloc[0]
        
        plt.bar(changes, values)
        plt.title(f'{student_name} 학생의 수업 전후 변화')
        plt.xticks(rotation=45, ha='right')
        plt.ylabel('변화 점수 (1-5)')
        plt.ylim(0, 5)
    
    elif chart_type == '문항별 상관관계':
        fig, ax = plt.subplots(figsize=(12, 10))
        survey_items = ['수업 기대도', '긴장도', '재미 예상도', '자신감', '집중도', 
                       '즐거움', '자신감 변화', '재미 변화', '긴장도 변화', '이해도']
        
        correlation_matrix = df[survey_items].corr()
        sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0, fmt='.2f')
        plt.title('문항별 상관관계')
    
    # 그래프를 base64로 인코딩
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=300)
    buf.seek(0)
    img_str = base64.b64encode(buf.getvalue()).decode()
    
    return img_str, None

def analyze_survey_data(spreadsheet_id, range_name, chart_type, student_name=None):
    """
    구글 스프레드시트에서 데이터를 가져와서 시각화를 생성합니다.
    """
    try:
        service = get_google_sheets_service()
        if service is None:
            return None, "구글 스프레드시트 서비스를 초기화할 수 없습니다. 인증 정보를 확인해주세요."
        
        df = get_sheet_data(service, spreadsheet_id, range_name)
        if df is None:
            return None, "데이터를 가져오는데 실패했습니다. 스프레드시트 ID와 범위가 올바른지 확인해주세요."
        
        img_str, error = create_visualization(df, chart_type, student_name)
        if error:
            return None, error
        
        return img_str, None
    except Exception as e:
        return None, f"분석 중 오류가 발생했습니다: {str(e)}"

def main():
    st.set_page_config(page_title="학생 설문 분석 MCP", layout="wide")
    
    st.title('📊 학생 설문 분석 MCP')
    
    # 사이드바 설정
    st.sidebar.title('설정')
    
    # Google API 인증 설정 섹션
    st.sidebar.header('Google API 인증')
    st.sidebar.markdown("""
    ### 인증 방법
    다음 중 한 가지 방법으로 Google API 인증 정보를 설정하세요:
    1. 환경 변수 `GOOGLE_CREDENTIALS_PATH`에 인증 파일 경로 설정
    2. 프로젝트 루트 디렉토리에 `credentials.json` 파일 위치시키기
    3. 아래 업로더를 통해 인증 파일 직접 업로드
    4. Streamlit Cloud를 사용하는 경우 `st.secrets`에 `GOOGLE_CREDENTIALS` 설정
    """)
    
    # 인증 파일 업로드 기능
    uploaded_file = st.sidebar.file_uploader("Google API 인증 파일 업로드", type=['json'])
    if uploaded_file is not None:
        # 파일을 임시로 저장
        with open('credentials.json', 'wb') as f:
            f.write(uploaded_file.getbuffer())
        st.sidebar.success("인증 파일이 성공적으로 업로드되었습니다.")
    
    # 구글 스프레드시트 ID 입력
    st.sidebar.header('스프레드시트 설정')
    spreadsheet_id = st.sidebar.text_input('구글 스프레드시트 ID를 입력하세요')
    range_name = st.sidebar.text_input('데이터 범위를 입력하세요 (예: Sheet1!A1:F100)')
    
    # 분석 유형 선택
    chart_options = ['문항별 평균 점수', '문항별 상관관계']
    if spreadsheet_id and range_name:
        service = get_google_sheets_service()
        if service:
            try:
                df = get_sheet_data(service, spreadsheet_id, range_name)
                if df is not None:
                    student_options = ['전체'] + df['학생 이름'].tolist()
                    chart_options = ['학생별 설문 응답', '학생별 변화 추이'] + chart_options
            except:
                student_options = ['전체']
        else:
            student_options = ['전체']
    else:
        student_options = ['전체']
    
    st.sidebar.header('분석 설정')
    chart_type = st.sidebar.selectbox('분석 유형을 선택하세요', chart_options)
    
    if '학생별' in chart_type:
        student_name = st.sidebar.selectbox('학생을 선택하세요', student_options[1:] if len(student_options) > 1 else [''])
    else:
        student_name = None
    
    if st.sidebar.button('분석 실행'):
        if spreadsheet_id and range_name:
            with st.spinner('데이터를 분석하는 중...'):
                img_str, error = analyze_survey_data(spreadsheet_id, range_name, chart_type, student_name)
                if img_str:
                    st.success('분석이 완료되었습니다!')
                    st.image(f"data:image/png;base64,{img_str}", use_column_width=True)
                    # 이미지 다운로드 링크 제공
                    st.markdown(f"[분석 결과 다운로드](data:image/png;base64,{img_str})", unsafe_allow_html=True)
                else:
                    st.error(error)
        else:
            st.error('스프레드시트 ID와 데이터 범위를 모두 입력해주세요.')
    
    # 앱 사용법 안내
    with st.expander("앱 사용 안내", expanded=False):
        st.markdown("""
        ### 사용 방법
        1. 사이드바에서 Google API 인증 정보를 설정합니다.
        2. 구글 스프레드시트 ID와 데이터 범위를 입력합니다.
        3. 분석 유형을 선택합니다.
        4. 학생별 분석인 경우 학생을 선택합니다.
        5. '분석 실행' 버튼을 클릭합니다.
        
        ### 인증 파일 얻는 방법
        1. [Google Cloud Console](https://console.cloud.google.com/)에 접속합니다.
        2. 프로젝트를 선택하거나 새 프로젝트를 만듭니다.
        3. Google Sheets API를 사용 설정합니다.
        4. 사용자 인증 정보 > 서비스 계정 > 키 만들기를 선택합니다.
        5. JSON 형식의 키를 다운로드합니다.
        """)

if __name__ == '__main__':
    main() 
