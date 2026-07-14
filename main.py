import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
from datetime import date, timedelta

# 페이지 기본 설정
st.set_page_config(page_title="주식 분석 대시보드", page_icon="📈", layout="wide")

st.title("📈 인터랙티브 주식 데이터 대시보드")
st.markdown("Yahoo Finance 데이터를 활용하여 주가 흐름과 거래량을 분석합니다.")

# 1. 사이드바 (사용자 입력 필드)
st.sidebar.header("검색 설정")
ticker = st.sidebar.text_input("주식 티커 입력 (예: AAPL, TSLA, 005930.KS)", "AAPL").upper()
start_date = st.sidebar.date_input("시작일", date.today() - timedelta(days=365))
end_date = st.sidebar.date_input("종료일", date.today())

# 2. 데이터 로드 함수 (캐싱하여 속도 최적화)
@st.cache_data
def load_data(ticker, start, end):
    stock = yf.Ticker(ticker)
    df = stock.history(start=start, end=end)
    df.reset_index(inplace=True)
    
    # Plotly 호환성을 위해 Date 컬럼의 시간대(timezone) 정보 제거
    if 'Date' in df.columns:
        df['Date'] = df['Date'].dt.tz_localize(None)
        
    return stock.info, df

# 3. 메인 화면 로직
if ticker:
    with st.spinner('데이터를 불러오는 중입니다...'):
        try:
            info, df = load_data(ticker, start_date, end_date)

            if df.empty:
                st.error("데이터를 찾을 수 없습니다. 올바른 티커 심볼이나 날짜 구간인지 확인해주세요.")
            else:
                # 기업 기본 정보 표시
                company_name = info.get('longName', ticker)
                current_price = info.get('currentPrice', '정보 없음')
                currency = info.get('currency', 'USD')

                st.subheader(f"🏢 {company_name} ({ticker})")
                if current_price != '정보 없음':
                    st.metric(label="현재가", value=f"{current_price:,.2f} {currency}")

                # 4. Plotly 캔들스틱 차트 생성 (주가 및 이동평균선)
                fig = go.Figure()

                # 캔들스틱
                fig.add_trace(go.Candlestick(
                    x=df['Date'],
                    open=df['Open'],
                    high=df['High'],
                    low=df['Low'],
                    close=df['Close'],
                    name='주가'
                ))

                # 이동평균선 계산 및 추가 (20일, 60일)
                df['MA20'] = df['Close'].rolling(window=20).mean()
                df['MA60'] = df['Close'].rolling(window=60).mean()

                fig.add_trace(go.Scatter(x=df['Date'], y=df['MA20'], line=dict(color='cyan', width=1.5), name='20일 이동평균선'))
                fig.add_trace(go.Scatter(x=df['Date'], y=df['MA60'], line=dict(color='orange', width=1.5), name='60일 이동평균선'))

                # 차트 레이아웃
                fig.update_layout(
                    title=f"{ticker} 주가 흐름 (캔들스틱)",
                    yaxis_title="주가",
                    xaxis_title="날짜",
                    xaxis_rangeslider_visible=False, # 하단 슬라이더 숨김 (깔끔한 UI)
                    template="plotly_dark", # 다크 테마 적용
                    height=600
                )
                st.plotly_chart(fig, use_container_width=True)

                # 5. 거래량 차트 (막대 그래프)
                st.subheader("📊 거래량 추이")
                fig_vol = go.Figure(data=[go.Bar(x=df['Date'], y=df['Volume'], marker_color='rgba(135, 206, 250, 0.6)', name='거래량')])
                fig_vol.update_layout(
                    height=250, 
                    margin=dict(l=0, r=0, t=30, b=0),
                    template="plotly_dark"
                )
                st.plotly_chart(fig_vol, use_container_width=True)

                # 6. 원시 데이터 확인
                with st.expander("테이블로 원시 데이터(Raw Data) 보기"):
                    # 최근 날짜가 위로 오도록 정렬
                    st.dataframe(df.sort_values('Date', ascending=False), use_container_width=True)

        except Exception as e:
            st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
