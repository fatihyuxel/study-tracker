"""
app.py — Çocuk Çalışma Takip Uygulaması
Streamlit + Google Sheets backend
Mobil uyumlu tasarım
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo

from config import (
    CHILDREN, DAY_NAMES, DAY_NAMES_SHORT, TR_TZ, EMOJI, COLORS,
    EXAM_TYPES,
)
from data import (
    ensure_sheets, today_str, today_weekday, is_holiday,
    get_logs, get_targets, get_subjects, get_holidays,
    get_child_subjects, get_today_targets, get_child_targets,
    get_entry_for_date_subject, get_entries_for_date,
    get_weekly_progress, get_streak, get_week_dates,
    save_log, update_log, save_targets,
    add_subject, remove_subject,
    add_holiday, remove_holiday,
    get_exam_logs, get_exam_results, get_exam_subjects,
    calculate_net, save_exam, get_child_exam_results, get_child_exam_logs,
)
from charts import (
    chart_daily_trend, chart_error_analysis,
    chart_subject_distribution, chart_weekly_target_comparison,
)


# ═══════════════════════════════════════════════════════════════
#  SAYFA AYARLARI
# ═══════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Çalışma Takip",
    page_icon="📚",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ─── Mobil uyumlu CSS ─────────────────────────────────────────
st.markdown("""
<style>
    /* Genel font büyütme (mobil okunabilirlik) */
    .stApp { font-size: 16px; }

    /* Metric kartları */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #1e1e2e 0%, #2a2a3e 100%);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }
    [data-testid="stMetric"] label {
        font-size: 0.85rem !important;
        color: #94a3b8 !important;
    }
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-size: 1.6rem !important;
        font-weight: 700 !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    }

    /* Butonlar */
    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        padding: 0.5rem 1.5rem;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }

    /* Form alanı */
    .stSelectbox, .stNumberInput, .stDateInput {
        border-radius: 8px;
    }

    /* Progress bar */
    .stProgress > div > div > div {
        border-radius: 8px;
    }

    /* Başarı/hata kutuları */
    .success-box {
        background: rgba(34,197,94,0.15);
        border: 1px solid rgba(34,197,94,0.3);
        border-radius: 10px;
        padding: 12px 16px;
        margin: 8px 0;
    }
    .warning-box {
        background: rgba(245,158,11,0.15);
        border: 1px solid rgba(245,158,11,0.3);
        border-radius: 10px;
        padding: 12px 16px;
        margin: 8px 0;
    }
    .danger-box {
        background: rgba(239,68,68,0.15);
        border: 1px solid rgba(239,68,68,0.3);
        border-radius: 10px;
        padding: 12px 16px;
        margin: 8px 0;
    }
    .info-box {
        background: rgba(59,130,246,0.15);
        border: 1px solid rgba(59,130,246,0.3);
        border-radius: 10px;
        padding: 12px 16px;
        margin: 8px 0;
    }

    /* Tatil banner */
    .holiday-banner {
        background: linear-gradient(135deg, #f59e0b 0%, #f97316 100%);
        color: white;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        font-size: 1.2rem;
        font-weight: 700;
        margin: 16px 0;
    }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
#  İLK KURULUM — Google Sheets sayfalarını oluştur
# ═══════════════════════════════════════════════════════════════

ensure_sheets()


# ═══════════════════════════════════════════════════════════════
#  SIDEBAR — Navigasyon
# ═══════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("## 📚 Çalışma Takip")
    st.markdown("---")

    # Session state'de sayfa yoksa default ayarla
    if "page" not in st.session_state:
        st.session_state.page = CHILDREN[0]

    # Çocuk butonları
    for child in CHILDREN:
        emoji = "👧" if child == "Ayşe Bade" else "👧"
        if st.button(
            f"{emoji} {child}",
            use_container_width=True,
            type="primary" if st.session_state.page == child else "secondary",
            key=f"nav_{child}",
        ):
            st.session_state.page = child

    st.markdown("")

    # Ebevyn butonu
    if st.button(
        "👨‍👩‍👧 Ebeveyn Paneli",
        use_container_width=True,
        type="primary" if st.session_state.page == "parent" else "secondary",
        key="nav_parent",
    ):
        st.session_state.page = "parent"

    st.markdown("---")
    st.caption(f"🕐 {datetime.now(ZoneInfo(TR_TZ)).strftime('%d.%m.%Y %H:%M')}")


# ═══════════════════════════════════════════════════════════════
#  ÇOCUK WORKSPACE
# ═══════════════════════════════════════════════════════════════

def show_child_workspace(child_name: str):
    """Çocuk ana sayfası."""
    today = today_str()
    weekday = today_weekday()
    day_name = DAY_NAMES[weekday]
    # Türkçe ay isimleri
    months_tr = {
        1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan",
        5: "Mayıs", 6: "Haziran", 7: "Temmuz", 8: "Ağustos",
        9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık"
    }
    now = datetime.now(ZoneInfo(TR_TZ))
    formatted_date = f"{now.day} {months_tr[now.month]} {now.year}"
    
    st.markdown(f"## {EMOJI['calendar']} {formatted_date} — {day_name}")
    st.markdown(f"### Hoş geldin, {child_name}! 👋")

    # ─── TATİL KONTROLÜ ──────────────────────────────────────
    holiday = is_holiday(today)
    if holiday:
        holidays_df = get_holidays()
        reason_row = holidays_df[holidays_df["Date"] == today]
        reason = reason_row.iloc[0]["Reason"] if not reason_row.empty else ""
        reason_text = f" — {reason}" if reason else ""
        st.markdown(f'<div class="holiday-banner">🏖️ Bugün tatil!{reason_text}<br>İstersen yine de çalışabilirsin 📖</div>',
                    unsafe_allow_html=True)

    # ─── PLAN KONTROLÜ ───────────────────────────────────────
    today_targets = get_today_targets(child_name)
    all_targets = get_child_targets(child_name)

    if all_targets.empty:
        st.markdown(f"""
        <div class="info-box">
            {EMOJI['plan']} <b>Henüz plan oluşturulmamış.</b><br>
            Ebevyn panelinden haftalık çalışma planın ayarlanacak.
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")
        _show_data_entry_form(child_name, today, [])
        _show_past_records(child_name)
        return

    # ─── BUGÜNKÜ İLERLEME KARTLARI ───────────────────────────
    if not holiday and not today_targets.empty:
        st.markdown(f"### {EMOJI['target']} Bugünkü Hedeflerin")

        today_logs = get_entries_for_date(child_name, today)

        for _, target_row in today_targets.iterrows():
            subject = target_row["Subject"]
            target_count = int(target_row["TargetCount"])

            # Bu dersteki bugünkü kayıt
            subj_log = today_logs[today_logs["Subject"] == subject]
            if not subj_log.empty:
                solved = int(subj_log.iloc[0]["Solved"])
            else:
                solved = 0

            pct = min(solved / target_count, 1.0) if target_count > 0 else 0

            # Renk ve durum
            if pct >= 1.0:
                color = COLORS["success"]
                status = f"{EMOJI['success']} Tamamlandı!"
            elif pct >= 0.7:
                color = COLORS["warning"]
                status = f"{EMOJI['warning']} Yaklaşıyorsun"
            else:
                color = COLORS["danger"]
                status = f"{EMOJI['danger']} Devam et"

            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{subject}** — {target_count} soru")
                st.progress(pct)
            with col2:
                st.markdown(f"<div style='text-align:center; padding-top:8px; color:{color}; font-weight:700;'>{int(pct*100)}%</div>",
                            unsafe_allow_html=True)

    # ─── STREAK + GENEL METRİKLER ────────────────────────────
    streak = get_streak(child_name)
    week_progress = get_weekly_progress(child_name)
    week_actual = sum(v[0] for v in week_progress.values())
    week_target = sum(v[1] for v in week_progress.values())
    week_pct = int(week_actual / week_target * 100) if week_target > 0 else 0

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🔥 Streak", f"{streak} gün")
    with col2:
        st.metric("📊 Haftalık", f"{week_pct}%")
    with col3:
        st.metric("📝 Bu Hafta", f"{week_actual} soru")

    st.markdown("---")

    # ─── VERİ GİRİŞİ FORMU ──────────────────────────────────
    _show_data_entry_form(child_name, today, today_targets)

    st.markdown("---")

    # ─── GEÇMİŞ KAYITLAR ─────────────────────────────────────
    _show_past_records(child_name)

    st.markdown("---")

    # ─── SINAV GİRİŞİ ────────────────────────────────────────
    _show_exam_entry(child_name)


# ─── Veri Giriş Formu ─────────────────────────────────────────

def _show_data_entry_form(child_name: str, today: str, today_targets):
    """Veri giriş formu."""
    st.markdown(f"### {EMOJI['pencil']} Soru Girişi")

    # Ders listesi: plan + subjects birleşimi
    planned_subjects = []
    if hasattr(today_targets, 'empty'):
        if not today_targets.empty:
            planned_subjects = today_targets["Subject"].tolist()
    elif today_targets:
        planned_subjects = today_targets

    all_subjects = get_child_subjects(child_name)
    # Birleştir, benzersiz ve isim sırasına göre sırala
    subject_list = sorted(set(planned_subjects + all_subjects))

    with st.form("data_entry", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            entry_date = st.date_input(
                "📅 Tarih",
                value=datetime.now(ZoneInfo(TR_TZ)).date(),
                max_value=datetime.now(ZoneInfo(TR_TZ)).date(),
                format="DD.MM.YYYY",
            )
        with col2:
            if subject_list:
                subject = st.selectbox("📚 Ders", subject_list)
            else:
                subject = st.text_input("📚 Ders adı")

        col1, col2, col3 = st.columns(3)
        with col1:
            solved = st.number_input("✅ Doğru Sayısı", min_value=0, step=1, value=0)
        with col2:
            incorrect = st.number_input("❌ Yanlış", min_value=0, step=1, value=0)
        with col3:
            blank = st.number_input("⬜ Boş", min_value=0, step=1, value=0)

        submitted = st.form_submit_button(f"{EMOJI['save']} Kaydet", use_container_width=True)

    if submitted:
        # Doğrulama
        if not subject or not subject.strip():
            st.error("Lütfen bir ders seçin veya yazın.")
            return

        if solved == 0 and incorrect == 0 and blank == 0:
            st.error("En az bir soru girmeniz gerekiyor.")
            return

        if incorrect + blank > solved:
            st.error(f"Yanlış ({incorrect}) + Boş ({blank}) = {incorrect + blank}, "
                     f"toplam soru sayısından ({solved}) büyük olamaz!")
            return

        date_str = entry_date.strftime("%Y-%m-%d")

        # Duplicate kontrolü
        existing = get_entry_for_date_subject(child_name, date_str, subject.strip())
        if existing:
            st.warning(
                f"{EMOJI['warning']} **{date_str}** tarihinde **{subject}** dersi için "
                f"zaten {existing['Solved']} soru girmişsiniz.\n\n"
                f"Mevcut kayıt güncellenecek."
            )
            update_log(child_name, date_str, subject.strip(), solved, incorrect, blank)
            st.success(f"{EMOJI['success']} Kayıt güncellendi!")
            st.rerun()
        else:
            save_log(child_name, date_str, subject.strip(), solved, incorrect, blank)
            st.success(f"{EMOJI['success']} Kayıt eklendi! {solved} soru kaydedildi.")
            st.rerun()


# ─── Geçmiş Kayıtlar ──────────────────────────────────────────

def _show_past_records(child_name: str):
    """Geçmiş kayıtları göster ve düzenlemeye izin ver."""
    st.markdown(f"### {EMOJI['calendar']} Geçmiş Kayıtlarım")

    logs = get_logs()
    if logs.empty:
        st.info("Henüz kayıt yok.")
        return

    child_logs = logs[logs["ChildName"] == child_name].copy()
    if child_logs.empty:
        st.info("Henüz kayıt yok.")
        return

    # Tarih seçici
    dates = sorted(child_logs["Date"].unique(), reverse=True)
    selected_date = st.selectbox("📅 Tarih seçin", dates, format_func=lambda d: _format_date_tr(d))

    if not selected_date:
        return

    entries = child_logs[child_logs["Date"] == selected_date]

    for _, row in entries.iterrows():
        subj = row["Subject"]
        solved = int(row["Solved"])
        incorrect = int(row["Incorrect"])
        blank = int(row["Blank"])
        net = solved - incorrect - blank

        with st.expander(f"📝 {subj} — {solved} doğru soru (Net: {net})", expanded=False):
            with st.form(f"edit_{selected_date}_{subj}", clear_on_submit=False):
                col1, col2, col3 = st.columns(3)
                with col1:
                    new_solved = st.number_input("Doğru", min_value=0, value=solved, key=f"s_{selected_date}_{subj}")
                with col2:
                    new_incorrect = st.number_input("Yanlış", min_value=0, value=incorrect, key=f"i_{selected_date}_{subj}")
                with col3:
                    new_blank = st.number_input("Boş", min_value=0, value=blank, key=f"b_{selected_date}_{subj}")

                if st.form_submit_button(f"{EMOJI['save']} Güncelle", use_container_width=True):
                    if new_incorrect + new_blank > new_solved:
                        st.error("Yanlış + Boş, doğru sayısından büyük olamaz!")
                    else:
                        update_log(child_name, selected_date, subj, new_solved, new_incorrect, new_blank)
                        st.success(f"{EMOJI['success']} Güncellendi!")
                        st.rerun()


def _format_date_tr(d: str) -> str:
    """YYYY-MM-DD → '19 Haziran 2026, Perşembe' formatı."""
    try:
        dt = datetime.strptime(d, "%Y-%m-%d")
        day_name = DAY_NAMES[dt.weekday()]
        months_tr = {
            1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan",
            5: "Mayıs", 6: "Haziran", 7: "Temmuz", 8: "Ağustos",
            9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık"
        }
        return f"{dt.day} {months_tr[dt.month]} {dt.year}, {day_name}"
    except Exception:
        return d


# ═══════════════════════════════════════════════════════════════
#  EBEVEYN PANELİ
# ═══════════════════════════════════════════════════════════════

def show_parent_dashboard():
    """Ebevyn ana paneli."""
    st.markdown(f"## 👨‍👩‍👧 Ebeveyn Paneli")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        f"{EMOJI['chart']} Analiz",
        f"{EMOJI['plan']} Haftalık Plan",
        f"{EMOJI['book']} Dersler",
        f"{EMOJI['holiday']} Tatiller",
        f"📊 Sınav Analizi",
    ])

    # ─── TAB 1: ANALİZ ───────────────────────────────────────
    with tab1:
        _show_analytics()

    # ─── TAB 2: HAFTALIK PLAN ────────────────────────────────
    with tab2:
        _show_plan_management()

    # ─── TAB 3: DERS YÖNETİMİ ────────────────────────────────
    with tab3:
        _show_subject_management()

    # ─── TAB 4: TATİL YÖNETİMİ ───────────────────────────────
    with tab4:
        _show_holiday_management()

    # ─── TAB 5: SINAV ANALİZİ ────────────────────────────────
    with tab5:
        _show_exam_analysis()


# ─── ANALİZ TAB'I ─────────────────────────────────────────────

def _show_analytics():
    """Performans analizi grafikleri."""
    logs = get_logs()

    if logs.empty:
        st.info("Henüz veri yok. Çocuklar veri girdikten sonra grafikler burada görünecek.")
        return

    # Filtreler
    col1, col2 = st.columns(2)
    with col1:
        child_filter = st.selectbox(
            "Çocuk",
            ["Tümü"] + CHILDREN,
            key="analytics_child",
        )
    with col2:
        dates = sorted(logs["Date"].unique())
        if len(dates) > 1:
            date_range = st.date_input(
                "Tarih Aralığı",
                value=(datetime.strptime(dates[0], "%Y-%m-%d").date(),
                       datetime.strptime(dates[-1], "%Y-%m-%d").date()),
                format="DD.MM.YYYY",
                key="analytics_dates",
            )
        else:
            date_range = None

    # Filtreleri uygula
    filtered = logs.copy()
    if child_filter != "Tümü":
        filtered = filtered[filtered["ChildName"] == child_filter]

    if date_range and len(date_range) == 2:
        start, end = date_range
        filtered = filtered[
            (filtered["Date"] >= start.strftime("%Y-%m-%d")) &
            (filtered["Date"] <= end.strftime("%Y-%m-%d"))
        ]

    if filtered.empty:
        st.info("Seçilen filtrelerde veri yok.")
        return

    # Metrikler
    total_solved = int(filtered["Solved"].sum())
    total_incorrect = int(filtered["Incorrect"].sum())
    total_blank = int(filtered["Blank"].sum())
    net = total_solved - total_incorrect - total_blank
    error_rate = ((total_incorrect + total_blank) / total_solved * 100) if total_solved > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📝 Toplam", f"{total_solved}")
    with col2:
        st.metric("✅ Net Doğru", f"{net}")
    with col3:
        st.metric("❌ Yanlış", f"{total_incorrect}")
    with col4:
        st.metric("⚠️ Hata Oranı", f"{error_rate:.0f}%")

    st.markdown("---")

    # Grafik 1: Trend
    children_for_chart = CHILDREN if child_filter == "Tümü" else [child_filter]
    st.plotly_chart(
        chart_daily_trend(filtered, children_for_chart),
        use_container_width=True,
        config=dict(displayModeBar=False, responsive=True),
    )

    # Grafik 2 ve 3 yan yana (mobilde alt alta düşer)
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(
            chart_error_analysis(filtered, child_filter if child_filter != "Tümü" else None),
            use_container_width=True,
            config=dict(displayModeBar=False, responsive=True),
        )
    with col2:
        st.plotly_chart(
            chart_subject_distribution(filtered, child_filter if child_filter != "Tümü" else None),
            use_container_width=True,
            config=dict(displayModeBar=False, responsive=True),
        )

    # Ham veri (isteğe bağlı)
    with st.expander("📋 Ham Veri Tablosu"):
        display_df = filtered.copy()
        display_df["Net"] = display_df["Solved"] - display_df["Incorrect"] - display_df["Blank"]
        st.dataframe(display_df, use_container_width=True, hide_index=True)


# ─── PLAN YÖNETİMİ TAB'I ─────────────────────────────────────

def _show_plan_management():
    """Haftalık plan yönetimi — her çocuk için grid."""
    for child in CHILDREN:
        st.markdown(f"### 👧 {child}")

        # Mevcut planı oku
        targets = get_child_targets(child)
        subjects = list(dict.fromkeys(get_child_subjects(child)))  # benzersiz

        if not subjects:
            st.info(f"{child} için henüz ders eklenmedi. 'Dersler' sekmesinden ekleyin.")
            st.markdown("---")
            continue

        # Mevcut planı dict'e çevir: {subject: {day: count}}
        current_plan = {}
        for subj in subjects:
            current_plan[subj] = {}
        if not targets.empty:
            for _, row in targets.iterrows():
                subj = row["Subject"]
                day = int(row["DayOfWeek"])
                count = int(row["TargetCount"])
                if subj not in current_plan:
                    current_plan[subj] = {}
                current_plan[subj][day] = count

        # Form: her ders bir expander içinde
        plan_data = {}
        with st.form(f"plan_form_{child}"):
            for subj in subjects:
                with st.expander(f"📚 {subj}", expanded=True):
                    cols = st.columns(7)
                    day_targets = {}
                    for d in range(7):
                        with cols[d]:
                            default_val = current_plan.get(subj, {}).get(d, 0)
                            val = st.number_input(
                                DAY_NAMES_SHORT[d],
                                min_value=0,
                                value=default_val,
                                key=f"plan_{child}_{subj}_{d}",
                            )
                            day_targets[d] = val
                    plan_data[subj] = day_targets

            if st.form_submit_button(f"{EMOJI['save']} Planı Kaydet", use_container_width=True):
                save_targets(child, plan_data)
                st.success(f"{EMOJI['success']} {child} için plan kaydedildi!")
                st.rerun()

        # Mevcut plan özeti
        if not targets.empty:
            st.markdown("**Mevcut plan özeti:**")
            summary_parts = []
            for subj in subjects:
                subj_targets = current_plan.get(subj, {})
                active_days = [DAY_NAMES_SHORT[d] for d, c in subj_targets.items() if c > 0]
                total = sum(subj_targets.values())
                if active_days:
                    summary_parts.append(f"- **{subj}**: {', '.join(active_days)} (toplam {total}/hafta)")
            if summary_parts:
                st.markdown("\n".join(summary_parts))

        st.markdown("---")


# ─── DERS YÖNETİMİ TAB'I ─────────────────────────────────────

def _show_subject_management():
    """Ders ekleme/silme."""
    for child in CHILDREN:
        st.markdown(f"### 👧 {child}")

        subjects = get_child_subjects(child)

        # Mevcut dersler
        if subjects:
            cols = st.columns(min(len(subjects), 4))
            for i, subj in enumerate(subjects):
                with cols[i % len(cols)]:
                    if st.button(
                        f"{EMOJI['delete']} {subj}",
                        key=f"del_subj_{child}_{subj}",
                        use_container_width=True,
                    ):
                        remove_subject(child, subj)
                        st.success(f"'{subj}' dersi silindi.")
                        st.rerun()
            st.caption("Silmek için derse tıklayın.")
        else:
            st.info("Henüz ders eklenmedi.")

        # Yeni ders ekle
        with st.form(f"add_subject_{child}", clear_on_submit=True):
            new_subject = st.text_input("Yeni ders adı", key=f"new_subj_{child}")
            if st.form_submit_button(f"{EMOJI['add']} Ders Ekle", use_container_width=True):
                if new_subject and new_subject.strip():
                    if new_subject.strip() in subjects:
                        st.warning("Bu ders zaten mevcut.")
                    else:
                        add_subject(child, new_subject.strip())
                        st.success(f"'{new_subject.strip()}' dersi eklendi!")
                        st.rerun()
                else:
                    st.error("Ders adı boş olamaz.")

        st.markdown("---")


# ─── TATİL YÖNETİMİ TAB'I ────────────────────────────────────

def _show_holiday_management():
    """Tatil günü ekleme/silme."""
    st.markdown("### 🏖️ Tatil Günleri")
    st.caption("Eklenen tatil günlerinde hedef sıfırlanır, çocuklar serbest giriş yapabilir.")

    holidays = get_holidays()

    # Mevcut tatiller
    if not holidays.empty:
        for _, row in holidays.iterrows():
            h_date = row["Date"]
            reason = row["Reason"]
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"📅 **{_format_date_tr(h_date)}** — {reason if reason else 'Tatil'}")
            with col2:
                if st.button(f"{EMOJI['delete']}", key=f"del_holiday_{h_date}"):
                    remove_holiday(h_date)
                    st.success(f"Tatil silindi: {h_date}")
                    st.rerun()
    else:
        st.info("Henüz tatil günü eklenmedi.")

    st.markdown("---")

    # Yeni tatil ekle
    with st.form("add_holiday", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            h_date = st.date_input(
                "Tatil tarihi",
                value=datetime.now(ZoneInfo(TR_TZ)).date(),
                format="DD.MM.YYYY",
                key="holiday_date",
            )
        with col2:
            reason = st.text_input("Sebep (opsiyonel)", key="holiday_reason",
                                   placeholder="Okul tatili, bayram, vb.")

        if st.form_submit_button(f"{EMOJI['add']} Tatil Ekle", use_container_width=True):
            date_str = h_date.strftime("%Y-%m-%d")
            if date_str in holidays["Date"].values:
                st.warning("Bu tarih zaten tatil olarak ekli.")
            else:
                add_holiday(date_str, reason.strip() if reason else "")
                st.success(f"{EMOJI['holiday']} Tatil eklendi: {_format_date_tr(date_str)}")
                st.rerun()


# ─── SINAV GİRİŞİ TAB'I ──────────────────────────────────────

def _show_exam_entry(child_name: str):
    """Deneme sınavı sonuçlarını gir."""
    st.markdown("### 📝 Deneme Sınavı Sonuçları")
    
    # Sınav türü seçimi (şimdilik sadece LGS)
    exam_type = EXAM_TYPES[0]  # LGS
    
    # Session state ile çift kaydı engelle
    if "exam_saved" not in st.session_state:
        st.session_state.exam_saved = False
    
    # Eğer vừa kaydedildiyse mesaj göster
    if st.session_state.exam_saved:
        st.success(f"{EMOJI['success']} Kayıt başarıyla tamamlandı! Yeni sınav girmek için formu doldurun.")
        st.session_state.exam_saved = False
    
    with st.form("exam_entry_form", clear_on_submit=True):
        # Sınav tarihi
        exam_date = st.date_input(
            "Sınav Tarihi",
            value=datetime.now(ZoneInfo(TR_TZ)).date(),
            format="DD.MM.YYYY",
        )
        
        # Sınav puanı ve sıralama
        col1, col2 = st.columns(2)
        with col1:
            score = st.number_input(
                "Sınav Puanı",
                min_value=0.0,
                max_value=500.0,
                value=0.0,
                step=0.001,
                format="%.3f",
            )
        with col2:
            rank = st.number_input(
                "Sıralama (Derece)",
                min_value=1,
                value=1,
                step=1,
            )
        
        # Ders bazlı sonuçlar
        st.markdown(f"#### 📚 {exam_type} Ders Sonuçları")
        
        subjects = get_exam_subjects(exam_type)
        subjects_data = []
        
        for subj_info in subjects:
            subject = subj_info["Subject"]
            total_q = subj_info["TotalQuestions"]
            
            st.markdown(f"**{subject}** ({total_q} soru)")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                correct = st.number_input(
                    "Doğru",
                    min_value=0,
                    max_value=total_q,
                    value=0,
                    key=f"exam_correct_{subject}",
                )
            with col2:
                incorrect = st.number_input(
                    "Yanlış",
                    min_value=0,
                    max_value=total_q,
                    value=0,
                    key=f"exam_incorrect_{subject}",
                )
            with col3:
                blank = st.number_input(
                    "Boş",
                    min_value=0,
                    max_value=total_q,
                    value=0,
                    key=f"exam_blank_{subject}",
                )
            
            # Net hesapla ve göster
            net = calculate_net(correct, incorrect)
            st.caption(f"Net: {net} | Toplam: {correct + incorrect + blank}/{total_q}")
            
            # Doğrulama
            if correct + incorrect + blank > total_q:
                st.error(f"⚠️ {subject}: Toplam soru sayısı {total_q}'ı geçemez!")
            
            subjects_data.append({
                "Subject": subject,
                "Correct": correct,
                "Incorrect": incorrect,
                "Blank": blank,
            })
        
        # Kaydet butonu
        submitted = st.form_submit_button(f"{EMOJI['save']} Sınav Sonuçlarını Kaydet", use_container_width=True, type="primary")
        
        if submitted:
            # Doğrulama
            total_correct = sum(d["Correct"] for d in subjects_data)
            total_incorrect = sum(d["Incorrect"] for d in subjects_data)
            total_blank = sum(d["Blank"] for d in subjects_data)
            
            if total_correct + total_incorrect + total_blank == 0:
                st.error("En az bir ders için veri girilmeli!")
            else:
                exam_date_str = exam_date.strftime("%Y-%m-%d")
                save_exam(child_name, exam_type, exam_date_str, score, rank, subjects_data)
                st.session_state.exam_saved = True
                st.rerun()


# ─── SINAV ANALİZİ TAB'I ─────────────────────────────────────

def _show_exam_analysis():
    """Sınav analizi grafikleri."""
    st.markdown("### 📊 Sınav Analizi")
    
    # Çocuk seçimi
    child_name = st.selectbox("Çocuk", CHILDREN, key="exam_analysis_child")
    
    # Sınav türü (şimdilik sadece LGS)
    exam_type = EXAM_TYPES[0]
    
    # Verileri çek
    results = get_child_exam_results(child_name, exam_type)
    exam_logs = get_child_exam_logs(child_name, exam_type=exam_type)
    
    if results.empty:
        st.info("Henüz sınav sonucu girilmemiş.")
        return
    
    # ─── SONUÇ TABLOSU ─────────────────────────────────────────
    st.markdown("#### 📋 Sınav Sonuçları")
    
    display_df = results[["ExamDate", "Score", "Rank"]].copy()
    display_df.columns = ["Tarih", "Puan", "Sıralama"]
    display_df["Tarih"] = display_df["Tarih"].apply(_format_date_tr)
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # ─── GRAFİKLER ─────────────────────────────────────────────
    if len(results) > 1:
        st.markdown("#### 📈 Trend Grafikleri")
        
        # Puan ve sıralama trendi
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Puan Trendi**")
            chart_data = results[["ExamDate", "Score"]].sort_values("ExamDate")
            chart_data["ExamDate"] = chart_data["ExamDate"].apply(
                lambda x: _format_date_tr(x).split(",")[0]
            )
            st.line_chart(chart_data.set_index("ExamDate")["Score"], use_container_width=True)
        
        with col2:
            st.markdown("**Sıralama Trendi** (Düşük = İyi)")
            chart_data = results[["ExamDate", "Rank"]].sort_values("ExamDate")
            chart_data["ExamDate"] = chart_data["ExamDate"].apply(
                lambda x: _format_date_tr(x).split(",")[0]
            )
            st.line_chart(chart_data.set_index("ExamDate")["Rank"], use_container_width=True)
    
    # ─── DERS BAZINDA NET ORTALAMASI ────────────────────────────
    if not exam_logs.empty:
        st.markdown("#### 📊 Ders Bazında Net Ortalaması")
        
        avg_nets = exam_logs.groupby("Subject")["Net"].mean().reset_index()
        avg_nets.columns = ["Ders", "Ortalama Net"]
        avg_nets = avg_nets.sort_values("Ortalama Net", ascending=False)
        
        st.bar_chart(avg_nets.set_index("Ders")["Ortalama Net"], use_container_width=True)
    
    # ─── SON SINAV DETAYI ───────────────────────────────────────
    if not exam_logs.empty:
        st.markdown("#### 🔍 Son Sınav Detayı")
        
        last_exam_date = results.iloc[0]["ExamDate"]
        last_exam = exam_logs[exam_logs["ExamDate"] == last_exam_date].copy()
        
        if not last_exam.empty:
            st.caption(f"Tarih: {_format_date_tr(last_exam_date)}")
            
            display_log = last_exam[["Subject", "Correct", "Incorrect", "Blank", "Net"]].copy()
            display_log.columns = ["Ders", "Doğru", "Yanlış", "Boş", "Net"]
            st.dataframe(display_log, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════
#  ANA YÖNLENDİRME
# ═══════════════════════════════════════════════════════════════

page = st.session_state.get("page", CHILDREN[0])

if page in CHILDREN:
    show_child_workspace(page)
elif page == "parent":
    show_parent_dashboard()
else:
    st.session_state.page = CHILDREN[0]
    st.rerun()
