import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
from datetime import date, timedelta

# 페이지 기본 설정
st.set_page_config(page_title="한국 AI & 반도체 주식 분석", page_icon="🇰🇷", layout="wide")

st.title("🇰🇷 한국 AI & 반도체 주식 대시보드")
st.markdown("대한민국을 대표하는 반도체(HBM, 파운드리) 및 인공지능(AI) 관련 기업들의 주가 흐름을 분석합니다.")

# 1. 한국 AI & 반도체 대표 종목 리스트 딕셔너리
KOR_STOCKS = {
    "삼성전자 (종합 반도체, AI 스마트폰)": "005930.KS",
    "SK하이닉스 (HBM, AI 메모리)": "000660.KS",
    "한미반도체 (HBM 핵심 공정 장비)": "042700.KS",
    "리노공업 (반도체 검사용 소켓)": "058470.KQ",
    "NAVER (한국형 초거대 AI 하이퍼클로바)": "035420.KS",
    "루닛 (의료 AI 진단 솔루션)": "328130.KQ",
    "솔트룩스 (AI 챗봇 및 언어모델)": "304100.KQ"
}

# 2. 사이드바 (종목 및 날짜 선택)
st.sidebar.header("🔍 분석 설정")
# 사용자가 직접 입력하지 않고 목록에서 선택하도록 변경
selected_name = st.sidebar.selectbox("분석할 기업을 선택하세요", list(KOR_STOCKS.keys()))
ticker = KOR_STOCKS[selected_name]

start_date = st.sidebar.date_input("시작일", date.today() - timedelta(days=365))
end_date = st.sidebar.date_input("종료일", date.today())

# 3. 데이터 로드 함수 (캐싱)
@st.cache_data
def load_data(ticker, start, end):
    stock = yf.Ticker(ticker)
    df = stock.history(start=start, end=end)
    df.reset_index(inplace=True)
    
    # Plotly 호환성을 위해 시간대(timezone) 정보 제거
    if 'Date' in df.columns:
        df['Date'] = df['Date'].dt.tz_localize(None)
        
    return stock.info, df

# 4. 메인 화면 로직
with st.spinner(f"'{selected_name}' 데이터를 불러오는 중입니다..."):
    try:
        info, df = load_data(ticker, start_date, end_date)

        if df.empty:
            st.error("데이터를 찾을 수 없습니다. 주말/공휴일이거나 해당 기간의 데이터가 없습니다.")
        else:
            # 상단 요약 정보 표시
            company_name = selected_name.split(" ")[0] # "삼성전자" 부분만 추출
            
            # yfinance에서 실시간 가격이나 전일 종가 가져오기
            current_price = info.get('currentPrice', df['Close'].iloc[-1])
            prev_close = info.get('previousClose', df['Close'].iloc[-2] if len(df) > 1 else current_price)
            
            # 등락률 계산
            price_change = current_price - prev_close
            percent_change = (price_change / prev_close) * 100

            st.subheader(f"🏢 {selected_name} ({ticker})")
            
            # 한국 원화(KRW)에 맞게 포맷팅하여 메트릭 표시
            st.metric(
                label="현재 주가", 
                value=f"₩ {int(current_price):,}", 
                delta=f"₩ {int(price_change):,} ({percent_change:.2f}%)"
            )

            # 5. Plotly 캔들스틱 차트 생성
            fig = go.Figure()

            # 캔들스틱 (상승은 빨간색, 하락은 파란색으로 한국식 색상 적용)
            fig.add_trace(go.Candlestick(
                x=df['Date'],
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name='주가',
                increasing_line_color='red',    # 한국 주식 시장 상승색
                decreasing_line_color='blue'    # 한국 주식 시장 하락색
            ))

            # 이동평균선 추가
            df['MA20'] = df['Close'].rolling(window=20).mean()
            df['MA60'] = df['Close'].rolling(window=60).mean()

            fig.add_trace(go.Scatter(x=df['Date'], y=df['MA20'], line=dict(color='#00FF00', width=1.5), name='20일 이동평균선'))
            fig.add_trace(go.Scatter(x=df['Date'], y=df['MA60'], line=dict(color='#FFD700', width=1.5), name='60일 이동평균선'))

            # 차트 디자인 설정
            fig.update_layout(
                title=f"{company_name} 주가 흐름",
                yaxis_title="주가 (KRW)",
                xaxis_title="날짜",
                xaxis_rangeslider_visible=False,
                template="plotly_dark",
                height=550,
                hovermode='x unified' # 마우스를 올렸을 때 정보를 한눈에 보여줌
            )
            st.plotly_chart(fig, use_container_width=True)

            # 6. 거래량 차트
            st.subheader("📊 거래량 추이")
            
            # 주가 상승/하락에 따른 거래량 막대 색상 지정 (한국식)
            colors = ['red' if df['Close'].iloc[i] >= df['Open'].iloc[i] else 'blue' for i in range(len(df))]
            
            fig_vol = go.Figure(data=[go.Bar(
                x=df['Date'], 
                y=df['Volume'], 
                marker_color=colors,
                opacity=0.6,
                name='거래량'
            )])
            fig_vol.update_layout(
                height=200, 
                margin=dict(l=0, r=0, t=30, b=0),
                template="plotly_dark",
                yaxis_title="거래량"
            )
            st.plotly_chart(fig_vol, use_container_width=True)

            # 7. 데이터 테이블 보기
            with st.expander("데이터 표로 보기 (클릭하여 펼치기)"):
                st.dataframe(
                    df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']].sort_values('Date', ascending=False),
                    use_container_width=True
                )

    except Exception as e:
        st.error(f"오류가 발생했습니다. 잠시 후 다시 시도해주세요. (에러: {e})")
