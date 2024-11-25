import streamlit as st

# HTML 파일 로드
html_file_path = "d:/py_codes/halluxCW/FAST/korea_birth_rate_map.html"

try:
    with open(html_file_path, "r", encoding="utf-8") as file:
        html_data = file.read()

    # Streamlit에서 렌더링
    st.set_page_config(layout="wide")
    st.title("시군구별 합계출산율 Choropleth 지도")
    st.components.v1.html(html_data, height=600, width=800)
except FileNotFoundError:
    st.error(f"파일이 존재하지 않습니다: {html_file_path}")

