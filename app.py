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
    Temporal <span style="color:#FF8C00;">Decay</span> &amp; Indifference
  </div>
  <div style="font-size:18px; font-weight:400; margin-top:2px;">
    the source of profit
  </div>
  <div style="font-size:13px; color:#999; margin-top:6px;">
    by <span style="color:#FF8C00; font-weight:600;">225NOW</span>
  </div>
  <div style="font-size:12px; color:#aaa; margin-top:10px;">
    時間的消耗と無関心が、利益の源泉である
  </div>
</div>
""", unsafe_allow_html=True)

import streamlit.components.v1 as components

def add_crash_events(fig, df, x_col: str, y_col: str, events_csv_path: str = "events.csv"):
    import numpy as np

    SHORT_LABEL = {
        "Lehman Collapse Shock": "LEH",
        "Bernanke Taper Shock": "TAPER",
        "Ebola Panic Shock": "EBOLA",
        "VIX Shock": "VIX",
        "COVID Outbreak Shock": "COVID",
        "Ukraine Invasion Shock": "UKR",
        "BOJ Rate Hike Shock": "BOJ",
        "Trump Tariff Shock": "TARIFF",
    }
    EVENT_RED = "#FF3B3B"

    # --- events 読み込み ---
    events = pd.read_csv(events_csv_path)
    events.columns = [c.strip() for c in events.columns]

    required = {"date", "shock", "opt_max_ret_pct"}
    if not required.issubset(set(events.columns)):
        st.error(f"{events_csv_path} must have columns: {sorted(required)} / now: {events.columns.tolist()}")
        st.stop()

    # 型整形
    events["date"] = pd.to_datetime(events["date"], errors="coerce")
    events["opt_max_ret_pct"] = pd.to_numeric(events["opt_max_ret_pct"], errors="coerce")

    # df 側も datetime に
    df[x_col] = pd.to_datetime(df[x_col], errors="coerce")

    # 欠損除外 & ソート（searchsortedの前提）
    df_sorted = df.dropna(subset=[x_col, y_col]).sort_values(x_col).reset_index(drop=True)
    events = events.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)

    if len(df_sorted) == 0 or len(events) == 0:
        return fig

    x_series = df_sorted[x_col]
    y_series = df_sorted[y_col]

    # --- イベント点のy座標：その日 / なければ直近過去 ---
    event_y = []
    for d in events["date"]:
        idx = x_series.searchsorted(d, side="right") - 1
        idx = max(0, min(idx, len(x_series) - 1))
        event_y.append(float(y_series.iloc[idx]))
    events["y"] = event_y

    # --- 縦線＋上ラベル ---
    for _, ev in events.iterrows():
        fig.add_vline(
            x=ev["date"],
            line_width=1,
            line_dash="dot",
            opacity=0.85,
            line_color=EVENT_RED
        )
        fig.add_annotation(
            x=ev["date"], y=1, xref="x", yref="paper",
            text=SHORT_LABEL.get(str(ev["shock"]), str(ev["shock"])),
            showarrow=False,
            yanchor="top",
            xanchor="left",
            font=dict(color=EVENT_RED, size=12)
        )

    # --- hover用：数値があるやつだけ ---
    hover_events = events.dropna(subset=["opt_max_ret_pct"]).copy()
    if len(hover_events) == 0:
        return fig

    fig.add_trace(go.Scatter(
        x=hover_events["date"],
        y=hover_events["y"],
        mode="markers",
        marker=dict(size=10, opacity=0.0, color=EVENT_RED),
        customdata=hover_events[["shock", "opt_max_ret_pct"]].to_numpy(),
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Max Option Return: %{customdata[1]:.0f}x<br>"
            "<extra></extra>"
        ),
        showlegend=False
    ))

    return fig



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

import streamlit.components.v1 as components

components.html("""
<div class="tradingview-widget-container">
  <div class="tradingview-widget-container__widget"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>
  {
    "symbols": [
      {"proName": "FOREXCOM:JP225", "title": "JP225 CFD"},
      {"proName": "FX:USDJPY", "title": "USDJPY"},
      {"proName": "OANDA:SPX500USD", "title": "SPX"},
      {"proName": "OANDA:XAUUSD", "title": "Gold"},
      {"proName": "BINANCE:BTCUSDT", "title": "Bitcoin"}
    ],
    "showSymbolLogo": true,
    "colorTheme": "dark",
    "isTransparent": true,
    "displayMode": "adaptive",
    "locale": "en"
  }
  </script>
</div>
""", height=70)



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
        mode="lines",          # ← 半角
        name=c,
        line=dict(color=colors[c], width=widths[c])
    ))

# ===== Crash Events Overlay =====
fig = add_crash_events(
    fig,
    df,
    x_col=date_col,
    y_col="①",               # ← 半角
    events_csv_path="events.csv"
)


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
    "JP225": "FOREXCOM:JP225",
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


st.markdown(
    """
    <div style="
        color: #FF3B3B;
        font-size: 13px;
        line-height: 1.75;
        margin-top: 48px;
        margin-bottom: 36px;
        padding: 22px 24px;
        border-left: 3px solid #FF3B3B;
        background: rgba(255,59,59,0.035);
    ">
     
    
    Money is not merely a medium of exchange, nor an object to be accumulated.<br>
    It is a medium that converts courage and risk-taking into real action.<br><br>

    That is why the concept of money never disappears in any era.<br>
    As long as uncertainty exists, there will always be those who accept it and those who avoid it.<br><br>

    <strong>Finance is a mechanism that concentrates money toward those with courage.</strong><br>
    This is not exploitation, but selection — a structure that allocates resources to those willing to bear uncertainty.<br><br>

    As a system that optimizes money toward courage, financial markets have driven human progress.<br>
    They are not merely arenas for monetary gambling.<br><br>

    <strong>This model is a tool to observe that world.</strong><br>
    Not to declare justice, nor to predict the future,<br>
    but to observe — structurally and calmly — the moments where fear, desire, time, and capital intersect.<br><br>

    
    マネーは、単なる交換手段でも、蓄積の対象でもない。<br>
    <strong>勇気とリスクテイクを、現実の行動へと変換するための媒介</strong>である。<br><br>

    だから、どんな時代においてもマネーの概念は消えない。<br>
    不確実性が存在する限り、それを引き受ける者と、回避する者は必ず分かれる。<br><br>

    <strong>金融とは、勇気ある者にマネーを集めるための収奪機能である。</strong><br>
    それは搾取ではない。不確実性を引き受ける覚悟を持つ者へ、<br>
    社会の資源を集中させるための構造である。<br><br>

    勇気ある者にマネーを最適化する装置としての金融市場は、<br>
    人類の発展そのものを駆動してきた。金融市場は、単なるマネーの賭博場ではない。<br><br>

    <strong>このモデルは、その世界を観測するためのツールである。</strong><br>
    正義を語るためでも、未来を断定するためでもない。<br>
    恐怖・欲望・時間・資本が交錯する瞬間を、構造として捉えるための観測装置である。
    </div>
    """,
    unsafe_allow_html=True
)



st.markdown(
    """
    <div style="
        color: #FF8C00;
        font-size: 11px;
        line-height: 1.55;
        opacity: 0.85;
        margin-top: 36px;
        padding-top: 16px;
        border-top: 1px solid rgba(255,140,0,0.25);
    ">
      <strong>Disclaimer:</strong><br>
      This site is provided for informational and educational purposes only and does not constitute investment advice, financial advice, or a recommendation to buy or sell any financial instruments.<br>
      All data and analysis are based on publicly available information and personal models. Past performance is not indicative of future results.<br>
      Use of this site is at your own risk.
      <br><br>
      <strong>Sharing / Redistribution:</strong><br>
      Do not reproduce, redistribute, republish, or share this content (including screenshots, data, charts, and text) without explicit permission from 225NOW.
      <br><br>
      <strong>【免責事項】</strong><br>
      本サイトは情報提供および教育目的のみを意図したものであり、投資助言、金融助言、または特定の金融商品や取引の売買を推奨するものではありません。<br>
      掲載されているデータおよび分析は、公開情報および個人的なモデルに基づいています。過去の実績は将来の成果を保証するものではありません。<br>
      本サイトの利用は、すべてご自身の判断と責任において行ってください。
      <br><br>
      <strong>【転載・無断拡散について】</strong><br>
      本コンテンツ（スクリーンショット、データ、チャート、文章を含む）の転載・再配布・再公開・共有は禁止します。共有が必要な場合は、事前に225NOWの許可を取得してください。
    </div>
    """,
    unsafe_allow_html=True
)


