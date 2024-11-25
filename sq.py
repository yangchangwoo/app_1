import zipfile
import os
import streamlit as st

# 압축 파일 경로
zip_file_path = "korea_birth_rate_map.zip"

try:
    # 압축 파일 읽기
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall()  # 현재 디렉토리에 압축 해제

    # HTML 파일 경로
    html_file_path = "korea_birth_rate_map.html"

    # HTML 내용 읽기
    with open(html_file_path, "r", encoding="utf-8") as file:
        html_data = file.read()

    # Streamlit에서 렌더링
    st.set_page_config(layout="wide")
    st.title("시군구별 합계출산율 Choropleth 지도")
    st.components.v1.html(html_data, height=600, width=800)

except Exception as e:
    st.error(f"파일을 처리하는 중 문제가 발생했습니다: {e}")
