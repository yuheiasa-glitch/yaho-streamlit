import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide")

# ===== ページ全体をブラックに =====
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600;700;800&display=swap');

/* 背景・色 */
.stApp {
    background-color: #000000;
    color: #e5e5e5;
}

/* フォントを全要素に強制適用 */
.stApp, .stApp * {
    font-family: 'IBM Plex Sans', system-ui, -apple-system, BlinkMacSystemFont, sans-serif !important;
    color: #e5e5e5;
}

/* Streamlit UIを消す */
[data-testid="stHeader"] { background: transparent; }
[data-testid="stToolbar"] { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ===== タイトル（英語主導）=====
st.markdown("""
<div style="margin-bottom:24px;">
  <div style="font-size:36px; font-weight:700; letter-spacing:0.5px;">
    Temporal Decay & Indifference
  </div>
  <div style="font-size:18px; font-weight:400; margin-top:2px;">
    the source of profit
  </div>
  <div style="font-size:13px; color:#999; margin-top:6px;">
    by 225NOW
  </div>
  <div style="font-size:12px; color:#aaa; margin-top:10px;">
    時間的消耗と無関心が、利益の源泉である
  </div>
</div>
"""
, unsafe_allow_html=True)

import streamlit.components.v1 as components

# ===== Spotify Podcast Embed =====
components.html(
    """
    <iframe
      style="border-radius:12px"
      src="https://open.spotify.com/embed/show/23KfzDdn2LBuF9tfj2NIsZ?utm_source=generator&theme=0"
      width="100%"
      height="152"
      frameBorder="0"
      allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
      loading="lazy">
    </iframe>
    """,
    height=170
)


# ===== CSV読み込み =====
df = pd.read_csv("data.csv")

# 列名の前後空白を除去
df.columns = [c.strip() for c in df.columns]

# 日付列を自動検出
date_candidates = ["日付", "date", "Date", "DATE"]
date_col = next((c for c in date_candidates if c in df.columns), None)

if date_col is None:
    st.error(f"日付列が見つからない。列名はこれ：{df.columns.tolist()}")
    st.stop()

# 日付をdatetime化
df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
df = df.dropna(subset=[date_col])

# ①②③列チェック
y_cols = ["①", "②", "③"]
missing = [c for c in y_cols if c not in df.columns]
if missing:
    st.error(f"①②③の列が足りない：{missing} / 列名はこれ：{df.columns.tolist()}")
    st.stop()

# ===== 色：①蛍光グリーン / ②グレー / ③白 =====
colors = {
    "①": "#FF8C00",  # オレンジ（Temporal Decay & Indifference）
    "②": "#A9B4C2",  # グレー
    "③": "#4A6FA5",  # 青鋼色（構造）
}
widths = {
    "①": 1.0,  # 主役だけ少し太く
    "②": 1.0,
    "③": 1.0,
}

# ===== Plotly =====
fig = go.Figure()
for c in y_cols:
    fig.add_trace(go.Scatter(
        x=df[date_col],
        y=df[c],
        mode="lines",
        name=c,
        line=dict(color=colors[c], width=widths[c])
    ))

fig.update_layout(
    height=520,
    paper_bgcolor="#000000",
    plot_bgcolor="#000000",
    font=dict(color="#e5e5e5"),
    margin=dict(l=40, r=60, t=10, b=40),

    xaxis=dict(
        gridcolor="#222",
        zerolinecolor="#222",
        tickfont=dict(color="#aaa"),

        # ★レンジボタンを見やすく（白系 + 暗文字）
        rangeselector=dict(
            bgcolor="rgba(255,255,255,0.92)",  # ボタン台を白寄りに
            activecolor="#7CFF4E",             # 選択中を蛍光グリーン
            bordercolor="rgba(255,255,255,0.55)",
            borderwidth=1,
            font=dict(color="#0A0A0A", size=12),
            buttons=[
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=3, label="3m", step="month", stepmode="backward"),
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(step="all", label="all")
            ],
        ),

        rangeslider=dict(
            visible=True,
            bgcolor="#000000",
            bordercolor="#333333"
        ),

        type="date"
    ),

yaxis=dict(
    gridcolor="#222",
    zeroline=True,
    zerolinecolor="#FFFFFF",   # 白（基準線）
    zerolinewidth=1.0,         # ← 少しだけ太く
    tickfont=dict(color="#aaa")
),

    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        font=dict(color="#aaaaaa"),
        orientation="v",
        x=1.02,
        y=0.95
    )
)

st.plotly_chart(fig, use_container_width=True)


# ===== Assets (TradingView) =====
st.markdown("<div style='height:22px'></div>", unsafe_allow_html=True)
st.markdown("### Assets", unsafe_allow_html=True)

ASSETS = {
    "Nikkei 225": "INDEX:NKY",
    "SPX": "OANDA:SPX500USD",
    "Gold": "OANDA:XAUUSD",
    "USDJPY": "FX:USDJPY",
    "Bitcoin": "BINANCE:BTCUSDT",
}
def tv_chart(symbol: str, height: int = 420):
    components.html(
        f"""
        <div class="tradingview-widget-container">
          <div class="tradingview-widget-container__widget"></div>
          <script type="text/javascript"
            src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js" async>
          {{
            "symbol": "{symbol}",
            "interval": "D",
            "timezone": "Asia/Tokyo",
            "theme": "dark",
            "style": "1",
            "locale": "en",
            "enable_publishing": false,
            "hide_top_toolbar": true,
            "hide_legend": true,
            "allow_symbol_change": false,
            "save_image": false,
            "withdateranges": true,
            "height": {height},
            "width": "100%"
          }}
          </script>
        </div>
        """,
        height=height + 20,
    )

tabs = st.tabs(list(ASSETS.keys()))
for tab, (name, symbol) in zip(tabs, ASSETS.items()):
    with tab:
        tv_chart(symbol, height=420)

# ===== News (TradingView) =====
st.markdown("<div style='height:22px'></div>", unsafe_allow_html=True)
st.markdown("### News", unsafe_allow_html=True)

components.html(
"""
<div class="tradingview-widget-container">
  <div class="tradingview-widget-container__widget"></div>
  <script type="text/javascript"
    src="https://s3.tradingview.com/external-embedding/embed-widget-timeline.js" async>
  {
    "feedMode": "market",
    "colorTheme": "dark",
    "isTransparent": true,
    "displayMode": "compact",
    "width": "100%",
    "height": 420,
    "locale": "en"
  }
  </script>
</div>
""",
height=440,
)