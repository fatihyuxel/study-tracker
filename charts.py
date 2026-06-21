"""
charts.py — Plotly grafik fonksiyonları (mobil uyumlu)
"""

import pandas as pd
import plotly.graph_objects as go
from config import CHART_COLORS, CHILDREN


# ─── Ortak tema ayarları ──────────────────────────────────────

_LAYOUT_DEFAULTS = dict(
    font=dict(size=13, color="#e2e8f0"),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=40, r=20, t=50, b=40),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=-0.25,
        xanchor="center",
        x=0.5,
    ),
)

_CONFIG = dict(
    displayModeBar=False,
    responsive=True,
)


def _apply_layout(fig: go.Figure, title: str, height: int = 350):
    """Ortak layout uygula."""
    fig.update_layout(
        **_LAYOUT_DEFAULTS,
        title=dict(text=title, font=dict(size=15)),
        height=height,
    )
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.1)")
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.1)")


# ═══════════════════════════════════════════════════════════════
#  GRAFİK 1: ÇİZGİ — Günlük Toplam Soru Trendi
# ═══════════════════════════════════════════════════════════════

def chart_daily_trend(logs: pd.DataFrame, children: list[str] = None) -> go.Figure:
    """
    Her çocuk için günlük toplam çözülen soru trendi.
    X ekseni: tarih, Y ekseni: toplam soru sayısı.
    """
    if children is None:
        children = CHILDREN

    fig = go.Figure()

    for i, child in enumerate(children):
        child_logs = logs[logs["ChildName"] == child].copy()
        if child_logs.empty:
            continue

        daily = child_logs.groupby("Date")["Solved"].sum().reset_index()
        daily = daily.sort_values("Date")

        fig.add_trace(go.Bar(
            x=daily["Date"],
            y=daily["Solved"],
            name=child,
            marker=dict(color=CHART_COLORS[i % len(CHART_COLORS)]),
        ))

    _apply_layout(fig, "📈 Günlük Soru Trendi")
    fig.update_xaxes(tickformat="%d %b", dtick=86400000)
    return fig


# ═══════════════════════════════════════════════════════════════
#  GRAFİK 2: BAR — Ders Bazlı Hata Oranı
# ═══════════════════════════════════════════════════════════════

def chart_error_analysis(logs: pd.DataFrame, child_name: str = None) -> go.Figure:
    """
    Ders bazlı hata oranı: (Yanlış + Boş) / Toplam × 100
    child_name belirtilmezse tüm çocuklar gösterilir.
    """
    df = logs.copy()
    if child_name:
        df = df[df["ChildName"] == child_name]

    if df.empty:
        fig = go.Figure()
        _apply_layout(fig, "🎯 Hata Analizi")
        return fig

    df["Total"] = df["Solved"] + df["Incorrect"] + df["Blank"]
    df["ErrorRate"] = ((df["Incorrect"] + df["Blank"]) / df["Total"].replace(0, 1)) * 100

    by_subject = df.groupby("Subject")["ErrorRate"].mean().reset_index()
    by_subject = by_subject.sort_values("ErrorRate", ascending=True)

    colors = [
        "#22c55e" if v < 20 else "#f59e0b" if v < 40 else "#ef4444"
        for v in by_subject["ErrorRate"]
    ]

    fig = go.Figure(go.Bar(
        x=by_subject["ErrorRate"],
        y=by_subject["Subject"],
        orientation="h",
        marker_color=colors,
        text=[f"{v:.0f}%" for v in by_subject["ErrorRate"]],
        textposition="outside",
    ))

    title = "🎯 Hata Oranı (Ders Bazlı)"
    if child_name:
        title += f" — {child_name}"

    _apply_layout(fig, title, height=max(250, len(by_subject) * 45 + 100))
    fig.update_xaxes(range=[0, 100])
    return fig


# ═══════════════════════════════════════════════════════════════
#  GRAFİK 3: PASTA — Ders Dağılımı
# ═══════════════════════════════════════════════════════════════

def chart_subject_distribution(logs: pd.DataFrame, child_name: str = None) -> go.Figure:
    """
    Ders bazlı çalışma dağılımı (toplam soru yüzdesi).
    """
    df = logs.copy()
    if child_name:
        df = df[df["ChildName"] == child_name]

    if df.empty:
        fig = go.Figure()
        _apply_layout(fig, "📚 Ders Dağılımı")
        return fig

    by_subject = df.groupby("Subject")["Solved"].sum().reset_index()

    fig = go.Figure(go.Pie(
        labels=by_subject["Subject"],
        values=by_subject["Solved"],
        hole=0.4,
        marker=dict(colors=CHART_COLORS[:len(by_subject)]),
        textinfo="label+percent",
        textposition="outside",
    ))

    title = "📚 Ders Dağılımı"
    if child_name:
        title += f" — {child_name}"

    _apply_layout(fig, title)
    return fig


# ═══════════════════════════════════════════════════════════════
#  GRAFİK 4: HAFTALIK HEDEF vs GERÇEKLEŞEN
# ═══════════════════════════════════════════════════════════════

def chart_weekly_target_comparison(
    progress: dict,
    child_name: str = ""
) -> go.Figure:
    """
    grouped bar: her ders için hedef vs gerçekleşen
    progress = {subject: (actual, target), ...}
    """
    if not progress:
        fig = go.Figure()
        _apply_layout(fig, "🎯 Haftalık Hedef vs Gerçekleşen")
        return fig

    subjects = list(progress.keys())
    actuals = [progress[s][0] for s in subjects]
    targets = [progress[s][1] for s in subjects]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Hedef",
        x=subjects,
        y=targets,
        marker_color="rgba(59,130,246,0.5)",
        marker_line=dict(color="#3b82f6", width=1),
    ))
    fig.add_trace(go.Bar(
        name="Gerçekleşen",
        x=subjects,
        y=actuals,
        marker_color="#22c55e",
    ))

    title = "🎯 Haftalık Hedef vs Gerçekleşen"
    if child_name:
        title += f" — {child_name}"

    _apply_layout(fig, title)
    fig.update_layout(barmode="group")
    return fig


# ═══════════════════════════════════════════════════════════════
#  BAHAR GRAFİKLERİ
# ═══════════════════════════════════════════════════════════════

def chart_bahar_books_daily(books: pd.DataFrame) -> go.Figure:
    """Bahar'ın günlük okuduğu sayfa trendi."""
    if books.empty:
        fig = go.Figure()
        _apply_layout(fig, "📚 Günlük Okunan Sayfa")
        return fig

    daily = books.groupby("Date")["PagesRead"].sum().reset_index()
    daily = daily.sort_values("Date")

    fig = go.Figure(go.Bar(
        x=daily["Date"],
        y=daily["PagesRead"],
        marker_color="#8b5cf6",
        text=daily["PagesRead"],
        textposition="outside",
    ))

    _apply_layout(fig, "📚 Günlük Okunan Sayfa")
    fig.update_xaxes(tickformat="%d %b", dtick=86400000)
    return fig


def chart_bahar_questions_daily(questions: pd.DataFrame) -> go.Figure:
    """Bahar'ın günlük çözdüğü soru trendi."""
    if questions.empty:
        fig = go.Figure()
        _apply_layout(fig, "📝 Günlük Çözülen Soru")
        return fig

    daily = questions.sort_values("Date")

    fig = go.Figure(go.Bar(
        x=daily["Date"],
        y=daily["TotalQuestions"],
        marker_color="#3b82f6",
        text=daily["TotalQuestions"],
        textposition="outside",
    ))

    _apply_layout(fig, "📝 Günlük Çözülen Soru")
    fig.update_xaxes(tickformat="%d %b", dtick=86400000)
    return fig
