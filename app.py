import streamlit as st

# 페이지 설정을 가장 먼저 실행
st.set_page_config(page_title="학생 설문 분석 MCP", layout="wide")

# 커스텀 CSS 스타일 정의
CUSTOM_CSS = """
<style>
.sidebar .sidebar-content {
    background-image: linear-gradient(#FFE2D1, #FFCAB0);
    color: #4F4F4F;
}
.Widget>label {
    font-size: 1.1rem;
    font-weight: 600;
    color: #5B3256;
}
.stButton>button {
    background-color: #F8A978;
    color: white;
    font-weight: bold;
    border-radius: 10px;
    border: none;
    padding: 0.5rem 1rem;
    transition: all 0.3s;
}
.stButton>button:hover {
    background-color: #FF8C61;
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}
.stTextInput>div>div>input, .stSelectbox>div>div>div {
    border-radius: 8px;
    border: 2px solid #FFD3B5;
}
[data-testid="stSidebar"] {
    background-color: #FFF1E6;
    padding: 1rem;
    border-radius: 0 10px 10px 0;
    box-shadow: 2px 0 10px rgba(0,0,0,0.1);
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1, 
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2, 
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 {
    color: #7D5A50;
    font-weight: 700;
}
[data-testid="stFileUploader"] {
    border-radius: 10px;
    background-color: #FFDDB5;
    padding: 1rem;
}
.stProgress > div > div > div > div {
    background-color: #F8A978;
}
.main-title {
    font-size: 2.5rem;
    color: #7D5A50;
    background: linear-gradient(45deg, #FF8C61, #F9C784);
    padding: 0.5rem 1rem;
    border-radius: 10px;
    margin-bottom: 2rem;
    text-align: center;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}
</style>
"""

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
import platform
import matplotlib.font_manager as fm
from matplotlib import font_manager, rc
import matplotlib as mpl

# 한글 폰트 설정
def set_korean_font():
    """한글 폰트를 설정하고 성공한 폰트 이름을 반환합니다."""
    try:
        # 기본 폰트 설정
        plt.rcParams['font.family'] = 'DejaVu Sans'
        plt.rcParams['axes.unicode_minus'] = False
        
        # 시스템에서 사용 가능한 폰트 찾기
        font_list = fm.findSystemFonts()
        
        # 선호하는 한글 폰트 목록
        preferred_fonts = ['NanumGothic', 'Malgun Gothic', 'AppleGothic', 'Noto Sans CJK KR']
        
        # 설치된 폰트 중에서 선호하는 폰트 찾기
        for font_name in preferred_fonts:
            matching_fonts = [f for f in font_list if font_name.lower() in f.lower()]
            if matching_fonts:
                font_path = matching_fonts[0]
                font_prop = fm.FontProperties(fname=font_path)
                plt.rcParams['font.family'] = font_prop.get_name()
                st.success(f"한글 폰트 '{font_name}' 적용 완료")
                return font_prop
        
        # 시스템에 설치된 모든 한글 폰트 찾기
        korean_fonts = [f for f in font_list if any(keyword in f.lower() for keyword in ['gothic', 'gulim', 'batang', 'dotum', 'korean'])]
        if korean_fonts:
            font_path = korean_fonts[0]
            font_prop = fm.FontProperties(fname=font_path)
            plt.rcParams['font.family'] = font_prop.get_name()
            st.success(f"시스템 한글 폰트 적용 완료: {os.path.basename(font_path)}")
            return font_prop
        
        st.warning("한글 폰트를 찾을 수 없어 기본 폰트를 사용합니다.")
        return fm.FontProperties(family='DejaVu Sans')
        
    except Exception as e:
        st.error(f"폰트 설정 중 오류 발생: {str(e)}")
        return fm.FontProperties(family='DejaVu Sans')

# 전역 폰트 설정
KOREAN_FONT = set_korean_font()

# seaborn 설정
sns.set_style("whitegrid")
sns.set_context("notebook", font_scale=1.2)

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
        # 스프레드시트 ID와 범위가 뒤바뀐 경우를 확인
        if '!' in spreadsheet_id and not '!' in range_name:
            # ID와 범위가 뒤바뀐 경우 교정
            spreadsheet_id, range_name = range_name, spreadsheet_id
            st.info("스프레드시트 ID와 범위가 교정되었습니다.")
        
        # 시트 이름에 특수 문자가 있는 경우 작은따옴표로 감싸기
        if '!' in range_name:
            sheet_name, cell_range = range_name.split('!', 1)
            if ('.' in sheet_name or ' ' in sheet_name) and not (sheet_name.startswith("'") and sheet_name.endswith("'")):
                sheet_name = f"'{sheet_name}'"
            range_name = f"{sheet_name}!{cell_range}"
        
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
        values = result.get('values', [])
        
        if not values:
            st.warning("데이터가 없습니다.")
            return None
        
        # 데이터프레임 생성 시 문자열 데이터 UTF-8로 인코딩 처리
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
            '😊 지금 수업이 즐거워요. (1점: 전혀 즐겁지 않아요 ~ 5점: 매우 즐거워요)': '즐거움',
            '🌟 이제 수학 공부에 자신감이 더 생겼어요. (1점: 전혀 그렇지 않아요 ~ 5점: 매우 그래요)': '자신감 변화',
            '🎉 수업 후에 수학이 전보다 더 재미있어졌어요. (1점: 전혀 그렇지 않아요 ~ 5점: 매우 그래요)': '재미 변화',
            '😌 수업 후에는 수학 시간에 전보다 덜 긴장돼요. (1점: 전혀 그렇지 않아요 ~ 5점: 매우 그래요)': '긴장도 변화',
            '🧠 오늘 수업 내용을 잘 이해했어요. (1점: 전혀 이해하지 못했어요 ~ 5점: 매우 잘 이해했어요)': '이해도',
            '📋 ✏️ 오늘 배운 수학 내용을 한 줄로 요약해 보세요.': '수업 요약',
            '📋 💭 오늘 수업에서 스스로 잘한 점이나 아쉬운 점을 한 문장으로 적어 보세요.': '자기 평가'
        }
        
        # 컬럼명 변경
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
    plt.close('all')
    
    # 그래프 생성
    fig = plt.figure(figsize=(12, 8), dpi=100)
    
    if chart_type == '학생별 설문 응답':
        if student_name is None:
            return None, "학생 이름을 지정해주세요."
        
        student_data = df[df['학생 이름'] == student_name]
        if student_data.empty:
            return None, f"'{student_name}' 학생을 찾을 수 없습니다."
        
        survey_items = ['수업 기대도', '긴장도', '재미 예상도', '자신감', '집중도', 
                       '즐거움', '자신감 변화', '재미 변화', '긴장도 변화', '이해도']
        values = student_data[survey_items].iloc[0]
        
        ax = fig.add_subplot(111)
        bars = ax.bar(range(len(survey_items)), values)
        
        # 한글 폰트 적용
        ax.set_title(f'{student_name} 학생의 설문 응답', fontsize=16, fontweight='bold', fontproperties=KOREAN_FONT)
        ax.set_xticks(range(len(survey_items)))
        ax.set_xticklabels(survey_items, rotation=45, ha='right', fontsize=10, fontproperties=KOREAN_FONT)
        ax.set_ylabel('점수 (1-5)', fontsize=12, fontproperties=KOREAN_FONT)
        ax.set_ylim(0, 5)
        
        # 막대 위에 값 표시
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}',
                   ha='center', va='bottom', fontproperties=KOREAN_FONT)
        
        # 자기 평가 정보 추가
        evaluation_text = f"\n수업 요약: {student_data['수업 요약'].iloc[0]}\n"
        evaluation_text += f"자기 평가: {student_data['자기 평가'].iloc[0]}"
        plt.figtext(0.02, 0.02, evaluation_text, fontsize=10, wrap=True, fontproperties=KOREAN_FONT)
    
    elif chart_type == '문항별 평균 점수':
        survey_items = ['수업 기대도', '긴장도', '재미 예상도', '자신감', '집중도', 
                       '즐거움', '자신감 변화', '재미 변화', '긴장도 변화', '이해도']
        
        means = df[survey_items].mean()
        stds = df[survey_items].std()
        
        ax = fig.add_subplot(111)
        bars = ax.bar(range(len(survey_items)), means, yerr=stds, capsize=5)
        
        ax.set_title('문항별 평균 점수 (오차 막대: 표준편차)', fontsize=16, fontweight='bold', fontproperties=KOREAN_FONT)
        ax.set_xticks(range(len(survey_items)))
        ax.set_xticklabels(survey_items, rotation=45, ha='right', fontsize=10, fontproperties=KOREAN_FONT)
        ax.set_ylabel('평균 점수 (1-5)', fontsize=12, fontproperties=KOREAN_FONT)
        ax.set_ylim(0, 5)
        
        # 막대 위에 값 표시
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.2f}',
                   ha='center', va='bottom', fontproperties=KOREAN_FONT)
    
    elif chart_type == '학생별 변화 추이':
        if student_name is None:
            return None, "학생 이름을 지정해주세요."
        
        student_data = df[df['학생 이름'] == student_name]
        if student_data.empty:
            return None, f"'{student_name}' 학생을 찾을 수 없습니다."
        
        changes = ['자신감 변화', '재미 변화', '긴장도 변화']
        values = student_data[changes].iloc[0]
        
        ax = fig.add_subplot(111)
        bars = ax.bar(range(len(changes)), values)
        
        ax.set_title(f'{student_name} 학생의 수업 전후 변화', fontsize=16, fontweight='bold', fontproperties=KOREAN_FONT)
        ax.set_xticks(range(len(changes)))
        ax.set_xticklabels(changes, rotation=45, ha='right', fontsize=12, fontproperties=KOREAN_FONT)
        ax.set_ylabel('변화 점수 (1-5)', fontsize=12, fontproperties=KOREAN_FONT)
        ax.set_ylim(0, 5)
        
        # 막대 위에 값 표시
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}',
                   ha='center', va='bottom', fontproperties=KOREAN_FONT)
    
    elif chart_type == '문항별 상관관계':
        survey_items = ['수업 기대도', '긴장도', '재미 예상도', '자신감', '집중도', 
                       '즐거움', '자신감 변화', '재미 변화', '긴장도 변화', '이해도']
        
        correlation_matrix = df[survey_items].corr()
        ax = fig.add_subplot(111)
        sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0, fmt='.2f', ax=ax)
        
        ax.set_title('문항별 상관관계', fontsize=16, fontweight='bold', fontproperties=KOREAN_FONT)
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right', fontsize=10, fontproperties=KOREAN_FONT)
        ax.set_yticklabels(ax.get_yticklabels(), fontsize=10, fontproperties=KOREAN_FONT)
    
    # 여백 조정
    plt.tight_layout(pad=3.0)
    
    # 그래프를 base64로 인코딩
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=300, facecolor='white')
    buf.seek(0)
    img_str = base64.b64encode(buf.getvalue()).decode()
    plt.close()
    
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
    # 커스텀 CSS 스타일 추가
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    
    st.markdown('<h1 class="main-title">📊 학생 설문 분석 MCP</h1>', unsafe_allow_html=True)
    
    # 사이드바 설정
    st.sidebar.title('🌈 설정')
    
    # Google API 인증 설정 섹션
    st.sidebar.header('🔐 Google API 인증')
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
        st.sidebar.success("인증 파일이 성공적으로 업로드되었습니다. ✅")
    
    # 구글 스프레드시트 ID 입력
    st.sidebar.header('📋 스프레드시트 설정')
    spreadsheet_id = st.sidebar.text_input('📝 스프레드시트 ID를 입력하세요')
    range_name = st.sidebar.text_input('📍 데이터 범위를 입력하세요 (예: Sheet1!A1:F100)')
    
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
    
    st.sidebar.header('📊 분석 설정')
    chart_type = st.sidebar.selectbox('📈 분석 유형을 선택하세요', chart_options)
    
    if '학생별' in chart_type:
        student_name = st.sidebar.selectbox('👨‍🎓 학생을 선택하세요', student_options[1:] if len(student_options) > 1 else [''])
    else:
        student_name = None
    
    if st.sidebar.button('✨ 분석 실행'):
        if spreadsheet_id and range_name:
            with st.spinner('데이터를 분석하는 중...'):
                img_str, error = analyze_survey_data(spreadsheet_id, range_name, chart_type, student_name)
                if img_str:
                    st.success('분석이 완료되었습니다!')
                    st.image(f"data:image/png;base64,{img_str}", use_container_width=True)
                    # 이미지 다운로드 링크 제공
                    st.markdown(f"[분석 결과 다운로드](data:image/png;base64,{img_str})", unsafe_allow_html=True)
                else:
                    st.error(error)
        else:
            st.error('스프레드시트 ID와 데이터 범위를 모두 입력해주세요.')
    
    # 앱 사용법 안내
    with st.expander("📚 앱 사용 안내", expanded=False):
        st.markdown("""
        <div style="background-color: #FFF1E6; padding: 20px; border-radius: 10px; border-left: 5px solid #F8A978;">
        <h3 style="color: #7D5A50;">🚀 사용 방법</h3>
        <ol style="color: #5B4B49;">
            <li>사이드바에서 Google API 인증 정보를 설정합니다. 🔐</li>
            <li>구글 스프레드시트 ID와 데이터 범위를 입력합니다. 📋</li>
            <li>분석 유형을 선택합니다. 📊</li>
            <li>학생별 분석인 경우 학생을 선택합니다. 👨‍🎓</li>
            <li>'분석 실행' 버튼을 클릭합니다. ✨</li>
        </ol>
        
        <h3 style="color: #7D5A50;">🔑 인증 파일 얻는 방법</h3>
        <ol style="color: #5B4B49;">
            <li><a href="https://console.cloud.google.com/" target="_blank">Google Cloud Console</a>에 접속합니다.</li>
            <li>프로젝트를 선택하거나 새 프로젝트를 만듭니다.</li>
            <li>Google Sheets API를 사용 설정합니다.</li>
            <li>사용자 인증 정보 > 서비스 계정 > 키 만들기를 선택합니다.</li>
            <li>JSON 형식의 키를 다운로드합니다.</li>
        </ol>
        </div>
        """, unsafe_allow_html=True)

if __name__ == '__main__':
    main() 
