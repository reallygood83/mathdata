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
        else:
            # 로컬 환경에서 실행 중인 경우
            credentials_path = os.getenv('GOOGLE_CREDENTIALS_PATH')
            if not credentials_path:
                st.error("GOOGLE_CREDENTIALS_PATH 환경 변수가 설정되지 않았습니다.")
                return None
            
            with open(credentials_path, 'r') as f:
                credentials_json = f.read()
        
        credentials = service_account.Credentials.from_service_account_info(
            json.loads(credentials_json), scopes=SCOPES)
        service = build('sheets', 'v4', credentials=credentials)
        return service
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
            return None, "구글 스프레드시트 서비스를 초기화할 수 없습니다."
        
        df = get_sheet_data(service, spreadsheet_id, range_name)
        if df is None:
            return None, "데이터를 가져오는데 실패했습니다."
        
        img_str, error = create_visualization(df, chart_type, student_name)
        if error:
            return None, error
        
        return img_str, None
    except Exception as e:
        return None, f"오류가 발생했습니다: {str(e)}"

def main():
    st.set_page_config(page_title="학생 설문 분석 MCP", layout="wide")
    
    st.title('📊 학생 설문 분석 MCP')
    
    # 사이드바 설정
    st.sidebar.title('설정')
    
    # 구글 스프레드시트 ID 입력
    spreadsheet_id = st.sidebar.text_input('구글 스프레드시트 ID를 입력하세요')
    range_name = st.sidebar.text_input('데이터 범위를 입력하세요 (예: Sheet1!A1:F100)')
    
    if st.sidebar.button('데이터 가져오기'):
        if spreadsheet_id and range_name:
            with st.spinner('데이터를 가져오는 중...'):
                img_str, error = analyze_survey_data(spreadsheet_id, range_name, '학생별 설문 응답')
                if img_str:
                    st.success('데이터를 성공적으로 가져왔습니다!')
                    st.image(img_str)
                else:
                    st.error(error)
        else:
            st.error('스프레드시트 ID와 데이터 범위를 입력해주세요.')

if __name__ == '__main__':
    main() 
