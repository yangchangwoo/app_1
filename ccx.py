import json
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import rc, font_manager
import streamlit as st
import altair as alt
import zipfile  
import os

# Streamlit 페이지 설정
st.set_page_config(
    page_title=" 범죄율 시각화 대시보드",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 폰트 설정
try:
    # 프로젝트 디렉터리에서 NanumGothic-Regular.ttf 로드
    font_path = "NanumGothic-Regular.ttf"  # GitHub에 업로드한 폰트 파일 이름
    if not os.path.exists(font_path):
        st.error("폰트 파일을 찾을 수 없습니다. GitHub에 NanumGothic-Regular.ttf를 업로드했는지 확인하세요.")
        st.stop()

    # 폰트 설정
    font_name = font_manager.FontProperties(fname=font_path).get_name()
    rc('font', family=font_name)
    plt.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 깨짐 방지
except Exception as e:
    st.error(f"폰트 설정 오류: {str(e)}")
    st.stop()


csv_path = "final.csv"
zip_path = "ctprvn.zip"

# CSV 데이터 로드
df = pd.read_csv(csv_path)
df = df.iloc[:, 1:]  # 첫 번째 열 제거
df = df.rename(columns={"발생지역별(1)": "city"})

# GeoJSON 데이터 로드

try:
    with zipfile.ZipFile(zip_path, 'r') as z:
        with z.open('ctprvn.json') as f:  # 압축 내부의 GeoJSON 파일 이름
            geo_gdf = gpd.read_file(f)
except FileNotFoundError:
    st.error("GeoJSON 압축 파일을 찾을 수 없습니다. 경로를 확인하세요.")
    st.stop()

# 지역 이름 매핑 테이블
city_name_mapping = {
    '서울': '서울특별시',
    '부산': '부산광역시',
    '대구': '대구광역시',
    '인천': '인천광역시',
    '광주': '광주광역시',
    '대전': '대전광역시',
    '울산': '울산광역시',
    '세종': '세종특별자치시',
    '경기': '경기도',
    '강원': '강원특별자치도',
    '충북': '충청북도',
    '충남': '충청남도',
    '전북': '전라북도',
    '전남': '전라남도',
    '경북': '경상북도',
    '경남': '경상남도',
    '제주': '제주특별자치도'
}

# DataFrame의 city 값 변경
df['city'] = df['city'].replace(city_name_mapping)

# 전년대비 증감률 계산
df['전년대비증감률'] = df.groupby(['city', 'category'])['value'].pct_change() * 100

# Sidebar: 연도 및 카테고리 선택
unique_years = sorted(df['year'].dropna().unique())
selected_year = st.sidebar.selectbox("연도 선택", unique_years, index=0)
selected_category = st.sidebar.selectbox("카테고리 선택", df['category'].unique())

# 특정 연도 및 카테고리 데이터 필터링
filtered_data = df[(df['category'] == selected_category) & (df['year'] == selected_year)]

# GeoDataFrame에 데이터 병합
geo_gdf = geo_gdf.merge(filtered_data, left_on='CTP_KOR_NM', right_on='city', how='left')

# NaN 값을 0으로 처리 (누락된 지역)
geo_gdf['value'] = geo_gdf['value'].fillna(0)

# 히트맵 생성 함수
def make_heatmap(input_df, input_y, input_x, input_color, input_color_theme):
    heatmap = alt.Chart(input_df).mark_rect().encode(
        y=alt.Y(f'{input_y}:O', axis=alt.Axis(title="연도", titleFontSize=18, titlePadding=15, titleFontWeight=900, labelAngle=0)),
        x=alt.X(f'{input_x}:O', axis=alt.Axis(title="지역", titleFontSize=18, titlePadding=15, titleFontWeight=900)),
        color=alt.Color(f'max({input_color}):Q',
                         legend=None,
                         scale=alt.Scale(scheme=input_color_theme)),
        stroke=alt.value('black'),
        strokeWidth=alt.value(0.25),
    ).properties(
        width=900,
        height=300
    ).configure_axis(
        labelFontSize=12,
        titleFontSize=12
    )
    return heatmap

# Streamlit 열 구성 (Column 1, Column 2, Column 3)
col1, col2, col3 = st.columns([1, 2, 1])


# 컬럼 1: 범죄 건수와 인구 수의 연관성
with col1:
    st.header("요약 정보")
    
    # 평균 값 계산
    mean_value = geo_gdf['value'].mean()
    st.metric("평균", f"{mean_value:.2f}")
    
    # 범죄 발생총건수 필터링
    crime_data = df[(df['category'] == '범죄 발생총건수') & (df['year'] == selected_year)]
    top_crime_regions = crime_data[['city', 'value']].sort_values(by='value', ascending=False).head(5)
    top_crime_regions = top_crime_regions.rename(columns={'value': '범죄 발생총건수'})
    
    # 총인구수 필터링
    population_data = df[(df['category'] == '총인구수') & (df['year'] == selected_year)]
    top_population_regions = population_data[['city', 'value']].sort_values(by='value', ascending=False).head(5)
    top_population_regions = top_population_regions.rename(columns={'value': '총인구수'})
    
    # 두 데이터프레임 병합 (비교)
    comparison_df = pd.merge(
        top_population_regions,  # 기준이 되는 데이터프레임을 총인구수로 설정
        top_crime_regions,
        on='city',
        how='outer',
        indicator=True
    )
    comparison_df['일치 여부'] = comparison_df['_merge'].map({
        'both': '일치',
        'left_only': '인구 수만 상위',
        'right_only': '범죄 건수만 상위'
    })
    comparison_df = comparison_df.drop(columns=['_merge'])
    
    # 총인구수 기준으로 정렬
    comparison_df = comparison_df.sort_values(by='총인구수', ascending=False)
    
    # 요약 정보 표시
    st.subheader("범죄 건수와 인구 수 연관성")
    for _, row in comparison_df.iterrows():
        st.write(
            f"**지역**: {row['city']} | **총인구수**: {row.get('총인구수', 'N/A')} | "
            f"**범죄 발생총건수**: {row.get('범죄 발생총건수', 'N/A')} | **일치 여부**: {row['일치 여부']}"
        )


# Column 2: 지도 및 히트맵 시각화
with col2:
    st.header("지도")
    # 지도 시각화
    fig, ax = plt.subplots(1, 1, figsize=(12, 10))
    geo_gdf.plot(
        column='value',
        cmap='YlOrRd',  # 색상 팔레트
        linewidth=0.8,
        ax=ax,
        edgecolor='0.8',
        legend=True
    )
    plt.title(f'{selected_year}년 {selected_category} (건/인구)', fontsize=16)
    plt.axis('off')  # 축 제거
    st.pyplot(fig)
    
    # 히트맵 생성 및 출력
    st.header("연도별 증감률 히트맵")
    heatmap = make_heatmap(
        input_df=df[df['category'] == selected_category],
        input_y='year',
        input_x='city',
        input_color='전년대비증감률',
        input_color_theme='blues'
    )
    st.altair_chart(heatmap, use_container_width=True)

# Column 3: 데이터 테이블 및 Top 5 도시
with col3:
    st.header("지역별 데이터")
    sorted_data = filtered_data.sort_values(by="value", ascending=False)
    st.dataframe(sorted_data[['city', 'value', '전년대비증감률']])
    
    st.header("Top 5 도시")
    top5 = sorted_data.head(5)
    st.table(top5[['city', 'value']])


