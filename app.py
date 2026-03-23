import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import streamlit.components.v1 as components

st.set_page_config(layout="wide")

# ===== Shared Layout Constants =====
CHART_HEIGHT = 520
CHART_MARGIN = dict(l=40, r=60, t=10, b=40)
CHART_TITLE_Y = 0.96

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


# ===== Utility Functions =====
def load_timeseries_csv(csv_path: str):
    df = pd.read_csv(csv_path)
    df.columns = [c.strip() for c in df.columns]

    date_candidates = ["日付", "date", "Date", "DATE"]
    date_col = next((c for c in date_candidates if c in df.columns), None)

    if date_col is None:
        st.error(f"{csv_path} に日付列が見つからない。列名: {df.columns.tolist()}")
        st.stop()

    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col]).sort_values(date_col).reset_index(drop=True)

    return df, date_col


def add_crash_events(fig, df, x_col: str, y_col: str, events_csv_path: str = "events.csv"):
    SHORT_LABEL = {
        "Lehman Collapse Shock": "LEH",
        "Bernanke Taper Shock": "TAPER",
        "Ebola Panic Shock": "EBOLA",
        "VIX Shock": "VIX",
        "COVID Outbreak Shock": "COVID",
        "Ukraine Invasion Shock": "UKR",
        "BOJ Rate Hike Shock": "BOJ",
        "Trump Tariff Shock": "TARIFF",
        "Brexit Shock": "BREX",
    }
    EVENT_RED = "#FF3B3B"

    events = pd.read_csv(events_csv_path)
    events.columns = [c.strip() for c in events.columns]

    required = {"date", "shock", "opt_max_ret_pct"}
    if not required.issubset(set(events.columns)):
        st.error(f"{events_csv_path} must have columns: {sorted(required)} / now: {events.columns.tolist()}")
        st.stop()

    events["date"] = pd.to_datetime(events["date"], errors="coerce")
    events["opt_max_ret_pct"] = pd.to_numeric(events["opt_max_ret_pct"], errors="coerce")

    df_local = df.copy()
    df_local[x_col] = pd.to_datetime(df_local[x_col], errors="coerce")
    df_local[y_col] = pd.to_numeric(df_local[y_col], errors="coerce")

    df_sorted = df_local.dropna(subset=[x_col, y_col]).sort_values(x_col).reset_index(drop=True)
    events = events.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)

    if len(df_sorted) == 0 or len(events) == 0:
        return fig

    x_series = df_sorted[x_col]
    y_series = df_sorted[y_col]

    event_y = []
    for d in events["date"]:
        idx = x_series.searchsorted(d, side="right") - 1
        idx = max(0, min(idx, len(x_series) - 1))
        event_y.append(float(y_series.iloc[idx]))
    events["y"] = event_y

    for _, ev in events.iterrows():
        fig.add_vline(
            x=ev["date"],
            line_width=1,
            line_dash="dot",
            opacity=0.85,
            line_color=EVENT_RED
        )
        fig.add_annotation(
            x=ev["date"],
            y=1,
            xref="x",
            yref="paper",
            text=SHORT_LABEL.get(str(ev["shock"]), str(ev["shock"])),
            showarrow=False,
            yanchor="top",
            xanchor="left",
            font=dict(color=EVENT_RED, size=12)
        )

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


def build_chart(
    df: pd.DataFrame,
    date_col: str,
    y_cols: list[str],
    colors: dict,
    widths: dict,
    title_text: str,
    title_color: str,
    height: int = CHART_HEIGHT,
    fill_col: str | None = None,
    fill_color: str = "rgba(170,120,255,0.12)",
    show_range_selector: bool = True,
    show_range_slider: bool = True,
    clip_y_quantile: float | None = None,
):
    fig = go.Figure()
    numeric_series_list = []

    for c in y_cols:
        series = pd.to_numeric(df[c], errors="coerce")
        numeric_series_list.append(series.dropna())

        if fill_col is not None and c == fill_col:
            fig.add_trace(go.Scatter(
                x=df[date_col],
                y=series,
                mode="lines",
                name=c,
                line=dict(color=colors[c], width=widths[c]),
                fill="tozeroy",
                fillcolor=fill_color,
            ))
        else:
            fig.add_trace(go.Scatter(
                x=df[date_col],
                y=series,
                mode="lines",
                name=c,
                line=dict(color=colors[c], width=widths[c]),
            ))

    xaxis_config = dict(
        showgrid=False,
        showline=True,
        linecolor="#444444",
        tickfont=dict(color="#a8a8a8"),
        type="date"
    )

    if show_range_selector:
        xaxis_config["rangeselector"] = dict(
            bgcolor="rgba(255,255,255,0.92)",
            activecolor="#7CFF4E",
            bordercolor="rgba(255,255,255,0.55)",
            borderwidth=1,
            font=dict(color="#0A0A0A", size=12),
            buttons=[
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=3, label="3m", step="month", stepmode="backward"),
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(step="all", label="all")
            ],
        )

    if show_range_slider:
        xaxis_config["rangeslider"] = dict(
            visible=True,
            bgcolor="#111111",
            bordercolor="#333333"
        )

    yaxis_config = dict(
        showgrid=True,
        gridcolor="#2a2a2a",
        zeroline=True,
        zerolinecolor="#666666",
        zerolinewidth=1.0,
        showline=True,
        linecolor="#444444",
        tickfont=dict(color="#a8a8a8"),
        autorange=True,
        fixedrange=False,
    )

    if clip_y_quantile is not None and 0 < clip_y_quantile < 0.5:
        all_vals = pd.concat(numeric_series_list, ignore_index=True)
        all_vals = all_vals.dropna()

        if len(all_vals) > 0:
            low = float(all_vals.quantile(clip_y_quantile))
            high = float(all_vals.quantile(1 - clip_y_quantile))
            if low < high:
                yaxis_config["range"] = [low, high]

    fig.update_layout(
        height=height,
        paper_bgcolor="#1c1c1c",
        plot_bgcolor="#111111",
        font=dict(color="#cfcfcf", size=12),
        margin=CHART_MARGIN,
        title=dict(
            text=title_text,
            x=0.01,
            y=CHART_TITLE_Y,
            xanchor="left",
            yanchor="top",
            font=dict(size=13, color=title_color)
        ),
        xaxis=xaxis_config,
        yaxis=yaxis_config,
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color="#aaaaaa"),
            orientation="v",
            x=1.02,
            y=0.95
        )
    )

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

# ===== Ticker Tape =====
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
df_jp, date_col_jp = load_timeseries_csv("jp_data.csv")
df_us, date_col_us = load_timeseries_csv("us_data.csv")
df_hsdx, date_col_hsdx = load_timeseries_csv("hsdx_data.csv")

# ===== JP列チェック =====
jp_cols = ["①", "②", "③"]
missing_jp = [c for c in jp_cols if c not in df_jp.columns]
if missing_jp:
    st.error(f"jp_data.csv に ①②③ が足りない: {missing_jp} / 列名: {df_jp.columns.tolist()}")
    st.stop()

# ===== US列チェック =====
us_cols = ["④", "⑤"]
missing_us = [c for c in us_cols if c not in df_us.columns]
if missing_us:
    st.error(f"us_data.csv に ④⑤ が足りない: {missing_us} / 列名: {df_us.columns.tolist()}")
    st.stop()

# ===== HSDX列チェック =====
hsdx_cols = ["⑥", "⑦"]
missing_hsdx = [c for c in hsdx_cols if c not in df_hsdx.columns]
if missing_hsdx:
    st.error(f"hsdx_data.csv に ⑥⑦ が足りない: {missing_hsdx} / 列名: {df_hsdx.columns.tolist()}")
    st.stop()

# ===== 色 =====
jp_colors = {
    "①": "#FF8C00",
    "②": "#A9B4C2",
    "③": "#4A6FA5",
}
jp_widths = {
    "①": 1.0,
    "②": 1.0,
    "③": 1.0,
}

us_colors = {
    "④": "#FFB01F",
    "⑤": "#6F8FEA",
}
us_widths = {
    "④": 1.0,
    "⑤": 1.0,
}

hsdx_colors = {
    "⑥": "#7CFF4E",
    "⑦": "#FF3B3B",
}
hsdx_widths = {
    "⑥": 1.2,
    "⑦": 1.0,
}

# ===== JP Chart =====
fig_jp = build_chart(
    df=df_jp,
    date_col=date_col_jp,
    y_cols=jp_cols,
    colors=jp_colors,
    widths=jp_widths,
    title_text="JP",
    title_color="#FF8C00",
    height=CHART_HEIGHT,
    fill_col="③",
    fill_color="rgba(170,120,255,0.12)",
    show_range_selector=True,
    show_range_slider=True,
    clip_y_quantile=None,
)

fig_jp = add_crash_events(
    fig_jp,
    df_jp,
    x_col=date_col_jp,
    y_col="①",
    events_csv_path="events.csv"
)

st.plotly_chart(fig_jp, use_container_width=True)

# ===== US Chart =====
st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

fig_us = build_chart(
    df=df_us,
    date_col=date_col_us,
    y_cols=us_cols,
    colors=us_colors,
    widths=us_widths,
    title_text="US",
    title_color="#4A6FA5",
    height=CHART_HEIGHT,
    fill_col=None,
    show_range_selector=True,
    show_range_slider=True,
    clip_y_quantile=None,
)

fig_us = add_crash_events(
    fig_us,
    df_us,
    x_col=date_col_us,
    y_col="④",
    events_csv_path="events.csv"
)

st.plotly_chart(fig_us, use_container_width=True)

# ===== HSDX Chart =====
st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

fig_hsdx = build_chart(
    df=df_hsdx,
    date_col=date_col_hsdx,
    y_cols=hsdx_cols,
    colors=hsdx_colors,
    widths=hsdx_widths,
    title_text="HSDX",
    title_color="#7CFF4E",
    height=CHART_HEIGHT,
    fill_col="⑥",
    fill_color="rgba(124,255,78,0.16)",
    show_range_selector=True,
    show_range_slider=True,
    clip_y_quantile=None,
)

st.plotly_chart(fig_hsdx, use_container_width=True)


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