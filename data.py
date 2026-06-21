"""
data.py — Google Sheets CRUD fonksiyonları
gspread + service account ile Streamlit entegrasyonu
"""

import streamlit as st
import gspread
import pandas as pd
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo

from config import (
    CHILDREN, TR_TZ, SHEET_NAMES,
    SHEET_LOGS, SHEET_TARGETS, SHEET_SUBJECTS, SHEET_HOLIDAYS,
    SHEET_EXAM_LOGS, SHEET_EXAM_RESULTS,
    LOGS_COLUMNS, TARGETS_COLUMNS, SUBJECTS_COLUMNS, HOLIDAYS_COLUMNS,
    EXAM_LOGS_COLUMNS, EXAM_RESULTS_COLUMNS,
    EXAM_STANDARDS,
)


# ═══════════════════════════════════════════════════════════════
#  BAĞLANTI
# ═══════════════════════════════════════════════════════════════

@st.cache_resource
def get_gspread_client() -> gspread.Client:
    """Service account ile Google Sheets bağlantısı (bir kez oluşturulur)."""
    creds = dict(st.secrets["gspread"])
    # private_key içindeki \n'leri düzelt (TOML'den gelirken escaped olabilir)
    if "\\n" in creds.get("private_key", ""):
        creds["private_key"] = creds["private_key"].replace("\\n", "\n")
    return gspread.service_account_from_dict(creds)


@st.cache_resource
def get_spreadsheet() -> gspread.Spreadsheet:
    """
    Ana spreadsheet'e bağlan. secrets.toml'da spreadsheet_key veya
    spreadsheet_url tanımlı olmalı.
    """
    gc = get_gspread_client()
    key = st.secrets.get("spreadsheet_key", "")
    url = st.secrets.get("spreadsheet_url", "")

    if key:
        return gc.open_by_key(key)
    elif url:
        return gc.open_by_url(url)
    else:
        st.error("❌ secrets.toml'da 'spreadsheet_key' veya 'spreadsheet_url' tanımlı değil!")
        st.stop()


# ═══════════════════════════════════════════════════════════════
#  SAYFA OLUŞTURMA (İLK KURULUM)
# ═══════════════════════════════════════════════════════════════

def ensure_sheets():
    """
    4 sayfanın (logs, targets, subjects, holidays) varlığını kontrol et.
    Yoksa oluştur ve başlıkları yaz.
    """
    sh = get_spreadsheet()
    existing = {ws.title for ws in sh.worksheets()}

    sheet_defs = {
        SHEET_LOGS:        LOGS_COLUMNS,
        SHEET_TARGETS:     TARGETS_COLUMNS,
        SHEET_SUBJECTS:    SUBJECTS_COLUMNS,
        SHEET_HOLIDAYS:    HOLIDAYS_COLUMNS,
        SHEET_EXAM_LOGS:   EXAM_LOGS_COLUMNS,
        SHEET_EXAM_RESULTS: EXAM_RESULTS_COLUMNS,
    }

    for name, columns in sheet_defs.items():
        if name not in existing:
            ws = sh.add_worksheet(title=name, rows=1000, cols=len(columns))
            ws.update(range_name="A1", values=[columns])
            ws.format("A1:Z1", {"textFormat": {"bold": True}})


# ═══════════════════════════════════════════════════════════════
#  YARDIMCI: SAYFA OKU → DataFrame
# ═══════════════════════════════════════════════════════════════

def _read_sheet(sheet_name: str, columns: list[str]) -> pd.DataFrame:
    """Bir sayfayı oku, DataFrame döndür. Boşsa boş DataFrame döndür."""
    sh = get_spreadsheet()
    try:
        ws = sh.worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        ensure_sheets()
        ws = sh.worksheet(sheet_name)

    records = ws.get_all_records()  # ilk satırı başlık olarak kullanır
    if not records:
        return pd.DataFrame(columns=columns)

    df = pd.DataFrame(records)
    # Eksik sütunları tamamla
    for col in columns:
        if col not in df.columns:
            df[col] = ""
    return df[columns]


# ═══════════════════════════════════════════════════════════════
#  CACHE'LI OKUMA FONKSİYONLARI
# ═══════════════════════════════════════════════════════════════

@st.cache_data(ttl=60)
def get_logs() -> pd.DataFrame:
    """Tüm log kayıtlarını oku."""
    df = _read_sheet(SHEET_LOGS, LOGS_COLUMNS)
    if not df.empty:
        df["Date"] = df["Date"].astype(str)
        for col in ["Solved", "Incorrect", "Blank"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    return df


@st.cache_data(ttl=60)
def get_targets() -> pd.DataFrame:
    """Tüm hedef kayıtlarını oku."""
    df = _read_sheet(SHEET_TARGETS, TARGETS_COLUMNS)
    if not df.empty:
        df["DayOfWeek"] = pd.to_numeric(df["DayOfWeek"], errors="coerce").fillna(0).astype(int)
        df["TargetCount"] = pd.to_numeric(df["TargetCount"], errors="coerce").fillna(0).astype(int)
    return df


@st.cache_data(ttl=60)
def get_subjects() -> pd.DataFrame:
    """Tüm ders listesini oku."""
    return _read_sheet(SHEET_SUBJECTS, SUBJECTS_COLUMNS)


@st.cache_data(ttl=60)
def get_holidays() -> pd.DataFrame:
    """Tüm tatil günlerini oku."""
    df = _read_sheet(SHEET_HOLIDAYS, HOLIDAYS_COLUMNS)
    if not df.empty:
        df["Date"] = df["Date"].astype(str)
    return df


def clear_all_caches():
    """Tüm cache'leri temizle (veri yazdıktan sonra çağrılır)."""
    get_logs.clear()
    get_targets.clear()
    get_subjects.clear()
    get_holidays.clear()
    get_exam_logs.clear()
    get_exam_results.clear()


# ═══════════════════════════════════════════════════════════════
#  TARİH YARDIMCILARI
# ═══════════════════════════════════════════════════════════════

def today_str() -> str:
    """Bugünün tarihi (Türkiye saati), YYYY-MM-DD formatında."""
    return datetime.now(ZoneInfo(TR_TZ)).strftime("%Y-%m-%d")


def today_weekday() -> int:
    """Bugünün gün numarası (0=Pazartesi ... 6=Pazar), Türkiye saati."""
    return datetime.now(ZoneInfo(TR_TZ)).weekday()


def parse_date(d) -> date:
    """String veya date objesini date'e çevir."""
    if isinstance(d, date):
        return d
    if isinstance(d, datetime):
        return d.date()
    return datetime.strptime(str(d).strip(), "%Y-%m-%d").date()


def is_holiday(check_date: str) -> bool:
    """Belirtilen tarih tatil mi?"""
    holidays = get_holidays()
    if holidays.empty:
        return False
    return check_date in holidays["Date"].values


# ═══════════════════════════════════════════════════════════════
#  DERS İŞLEMLERİ
# ═══════════════════════════════════════════════════════════════

def get_child_subjects(child_name: str) -> list[str]:
    """Bir çocuğun ders listesini döndür."""
    df = get_subjects()
    if df.empty:
        return []
    return sorted(df[df["ChildName"] == child_name]["Subject"].tolist())


def add_subject(child_name: str, subject: str):
    """Derse ekle."""
    sh = get_spreadsheet()
    ws = sh.worksheet(SHEET_SUBJECTS)
    ws.append_row([child_name, subject])
    clear_all_caches()


def remove_subject(child_name: str, subject: str):
    """Dersi sil."""
    sh = get_spreadsheet()
    ws = sh.worksheet(SHEET_SUBJECTS)
    df = get_subjects()

    # Silinecek satırı bul (1-indexed, +1 başlık satırı)
    mask = (df["ChildName"] == child_name) & (df["Subject"] == subject)
    indices = df[mask].index.tolist()

    # Tersten sil (satır numaraları kaymasın)
    for idx in reversed(indices):
        ws.delete_rows(idx + 2)  # +2: 0-indexed + başlık satırı

    clear_all_caches()


# ═══════════════════════════════════════════════════════════════
#  HEDEF (TARGET) İŞLEMLERİ
# ═══════════════════════════════════════════════════════════════

def get_child_targets(child_name: str) -> pd.DataFrame:
    """Bir çocuğun tüm hedeflerini döndür."""
    df = get_targets()
    if df.empty:
        return pd.DataFrame(columns=TARGETS_COLUMNS)
    return df[df["ChildName"] == child_name].copy()


def get_today_targets(child_name: str) -> pd.DataFrame:
    """Bugünün hedeflerini döndür (tatil günü ise boş)."""
    if is_holiday(today_str()):
        return pd.DataFrame(columns=TARGETS_COLUMNS)

    df = get_child_targets(child_name)
    if df.empty:
        return df

    weekday = today_weekday()
    return df[df["DayOfWeek"] == weekday].copy()


def save_targets(child_name: str, plan: dict):
    """
    Bir çocuğun haftalık planını kaydet.
    plan = {subject: {day_of_week: target_count, ...}, ...}
    Önce mevcut hedefleri sil, sonra yenisini yaz.
    """
    sh = get_spreadsheet()
    ws = sh.worksheet(SHEET_TARGETS)
    df = get_targets()

    # Mevcut hedefleri sil
    if not df.empty:
        mask = df["ChildName"] == child_name
        indices = df[mask].index.tolist()
        for idx in reversed(indices):
            ws.delete_rows(idx + 2)

    # Yeni hedefleri yaz
    rows = []
    for subject, day_targets in plan.items():
        for day_of_week, count in day_targets.items():
            if count > 0:  # 0 olanları yazma (o gün çalışılmayacak)
                rows.append([child_name, subject, day_of_week, count])

    if rows:
        ws.append_rows(rows)

    clear_all_caches()


# ═══════════════════════════════════════════════════════════════
#  LOG (VERİ GİRİŞİ) İŞLEMLERİ
# ═══════════════════════════════════════════════════════════════

def get_entry_for_date_subject(child_name: str, entry_date: str, subject: str) -> dict | None:
    """Belirli tarih+çocuk+ders kaydını bul. Yoksa None."""
    df = get_logs()
    if df.empty:
        return None

    mask = (
        (df["ChildName"] == child_name) &
        (df["Date"] == entry_date) &
        (df["Subject"] == subject)
    )
    matches = df[mask]
    if matches.empty:
        return None

    row = matches.iloc[0]
    return {
        "Solved": int(row["Solved"]),
        "Incorrect": int(row["Incorrect"]),
        "Blank": int(row["Blank"]),
    }


def get_entries_for_date(child_name: str, entry_date: str) -> pd.DataFrame:
    """Belirli bir tarihteki tüm kayıtları döndür."""
    df = get_logs()
    if df.empty:
        return pd.DataFrame(columns=LOGS_COLUMNS)

    mask = (df["ChildName"] == child_name) & (df["Date"] == entry_date)
    return df[mask].copy()


def save_log(child_name: str, entry_date: str, subject: str,
             solved: int, incorrect: int, blank: int, force_update: bool = False):
    """
    Veri girişini kaydet. Aynı tarih+çocuk+ders varsa:
    - force_update=True → üzerine yaz
    - force_update=False → hata fırlat (çağrı kontrol etsin)
    """
    existing = get_entry_for_date_subject(child_name, entry_date, subject)

    sh = get_spreadsheet()
    ws = sh.worksheet(SHEET_LOGS)

    if existing is not None and force_update:
        # Mevcut satırı bul ve güncelle
        df = get_logs()
        mask = (
            (df["ChildName"] == child_name) &
            (df["Date"] == entry_date) &
            (df["Subject"] == subject)
        )
        idx = df[mask].index[0] + 2  # +2: 0-indexed + başlık
        ws.update(range_name=f"A{idx}:F{idx}",
                  values=[[entry_date, child_name, subject, solved, incorrect, blank]])
    elif existing is not None:
        raise ValueError("duplicate")
    else:
        ws.append_row([entry_date, child_name, subject, solved, incorrect, blank])

    clear_all_caches()


def update_log(child_name: str, entry_date: str, subject: str,
               solved: int, incorrect: int, blank: int):
    """Mevcut kaydı güncelle (zorunlu)."""
    df = get_logs()
    if df.empty:
        return

    sh = get_spreadsheet()
    ws = sh.worksheet(SHEET_LOGS)

    mask = (
        (df["ChildName"] == child_name) &
        (df["Date"] == entry_date) &
        (df["Subject"] == subject)
    )
    matches = df[mask]
    if matches.empty:
        return

    idx = matches.index[0] + 2
    ws.update(range_name=f"A{idx}:F{idx}",
              values=[[entry_date, child_name, subject, solved, incorrect, blank]])

    clear_all_caches()


# ═══════════════════════════════════════════════════════════════
#  TATİL İŞLEMLERİ
# ═══════════════════════════════════════════════════════════════

def add_holiday(holiday_date: str, reason: str = ""):
    """Tatil günü ekle."""
    sh = get_spreadsheet()
    ws = sh.worksheet(SHEET_HOLIDAYS)
    ws.append_row([holiday_date, reason])
    clear_all_caches()


def remove_holiday(holiday_date: str):
    """Tatil gününü sil."""
    sh = get_spreadsheet()
    ws = sh.worksheet(SHEET_HOLIDAYS)
    df = get_holidays()

    if df.empty:
        return

    indices = df[df["Date"] == holiday_date].index.tolist()
    for idx in reversed(indices):
        ws.delete_rows(idx + 2)

    clear_all_caches()


# ═══════════════════════════════════════════════════════════════
#  İSTATİSTİK YARDIMCILARI
# ═══════════════════════════════════════════════════════════════

def get_week_dates() -> list[str]:
    """Bu haftanın tarihlerini döndür (Pazartesi→Pazar), YYYY-MM-DD."""
    today = datetime.now(ZoneInfo(TR_TZ)).date()
    monday = today - timedelta(days=today.weekday())
    return [(monday + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]


def get_weekly_progress(child_name: str) -> dict:
    """
    Haftalık ilerleme: her ders için {subject: (actual, target)} döndür.
    actual = bu hafta o derste çözülen toplam soru
    target = planlanan toplam hedef
    """
    targets = get_child_targets(child_name)
    logs = get_logs()
    week_dates = set(get_week_dates())

    if targets.empty:
        return {}

    # Hedefleri hesapla (haftalık toplam)
    target_by_subject = {}
    for _, row in targets.iterrows():
        subj = row["Subject"]
        target_by_subject[subj] = target_by_subject.get(subj, 0) + int(row["TargetCount"])

    # Gerçekleşenleri hesapla
    actual_by_subject = {}
    if not logs.empty:
        mask = (logs["ChildName"] == child_name) & (logs["Date"].isin(week_dates))
        week_logs = logs[mask]
        for _, row in week_logs.iterrows():
            subj = row["Subject"]
            actual_by_subject[subj] = actual_by_subject.get(subj, 0) + int(row["Solved"])

    # Birleştir
    result = {}
    for subj in target_by_subject:
        result[subj] = (actual_by_subject.get(subj, 0), target_by_subject[subj])

    return result


def get_streak(child_name: str) -> int:
    """
    Ardışık gün streak'i hesaplar.
    Bir gün "tamamlanmış" sayılır: o günün tüm planlı derslerinde
    en az bir kayıt varsa.
    """
    targets = get_child_targets(child_name)
    logs = get_logs()

    if targets.empty:
        return 0

    # Hangi günlerin planı var?
    scheduled_days = set(targets["DayOfWeek"].tolist())

    today = datetime.now(ZoneInfo(TR_TZ)).date()
    streak = 0

    for i in range(1, 365):  # max 1 yıl geriye bak
        check = today - timedelta(days=i)
        check_str = check.strftime("%Y-%m-%d")
        check_weekday = check.weekday()

        # Tatil günü → streak devam eder
        if is_holiday(check_str):
            streak += 1
            continue

        # Bu günün planı yoksa → streak devam eder (çalışma günü değil)
        if check_weekday not in scheduled_days:
            continue

        # Bu günün planlı dersleri
        day_targets = targets[targets["DayOfWeek"] == check_weekday]["Subject"].tolist()

        # Bu günün kayıtları
        if logs.empty:
            break
        mask = (logs["ChildName"] == child_name) & (logs["Date"] == check_str)
        day_subjects = set(logs[mask]["Subject"].tolist())

        # Tüm planlı dersler girilmiş mi?
        if all(subj in day_subjects for subj in day_targets):
            streak += 1
        else:
            break

    return streak


# ═══════════════════════════════════════════════════════════════
#  SINAV İŞLEMLERİ
# ═══════════════════════════════════════════════════════════════

@st.cache_data(ttl=60)
def get_exam_logs() -> pd.DataFrame:
    """Tüm sınav ders loglarını oku."""
    df = _read_sheet(SHEET_EXAM_LOGS, EXAM_LOGS_COLUMNS)
    if not df.empty:
        df["ExamDate"] = df["ExamDate"].astype(str)
        for col in ["Correct", "Incorrect", "Blank"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
        df["Net"] = pd.to_numeric(df["Net"], errors="coerce").fillna(0.0)
    return df


@st.cache_data(ttl=60)
def get_exam_results() -> pd.DataFrame:
    """Tüm sınav sonuçlarını (puan + sıralama) oku."""
    df = _read_sheet(SHEET_EXAM_RESULTS, EXAM_RESULTS_COLUMNS)
    if not df.empty:
        df["ExamDate"] = df["ExamDate"].astype(str)
        df["Score"] = pd.to_numeric(df["Score"], errors="coerce").fillna(0.0)
        df["Rank"] = pd.to_numeric(df["Rank"], errors="coerce").fillna(0).astype(int)
    return df


def get_exam_subjects(exam_type: str) -> list[dict]:
    """Belirli bir sınav türünün derslerini ve soru sayılarını döndür."""
    return EXAM_STANDARDS.get(exam_type, [])


def calculate_net(correct: int, incorrect: int) -> float:
    """Net hesapla: Net = Doğru - (Yanlış / 3)"""
    return round(correct - (incorrect / 3), 1)


def save_exam(child_name: str, exam_type: str, exam_date: str,
              score: float, rank: int, subjects_data: list[dict]):
    """
    Sınav sonucunu kaydet.
    subjects_data = [{"Subject": "...", "Correct": N, "Incorrect": N, "Blank": N}, ...]
    """
    sh = get_spreadsheet()
    
    # 1. ExamResults'e kaydet (puan + sıralama)
    ws_results = sh.worksheet(SHEET_EXAM_RESULTS)
    ws_results.append_row([exam_date, child_name, exam_type, score, rank])
    
    # 2. ExamLogs'a kaydet (ders bazlı)
    ws_logs = sh.worksheet(SHEET_EXAM_LOGS)
    rows = []
    for subj_data in subjects_data:
        correct = subj_data["Correct"]
        incorrect = subj_data["Incorrect"]
        blank = subj_data["Blank"]
        net = calculate_net(correct, incorrect)
        rows.append([exam_date, child_name, exam_type, 
                     subj_data["Subject"], correct, incorrect, blank, net])
    
    if rows:
        ws_logs.append_rows(rows)
    
    clear_all_caches()


def get_child_exam_results(child_name: str, exam_type: str = None) -> pd.DataFrame:
    """Bir çocuğun sınav sonuçlarını döndür."""
    df = get_exam_results()
    if df.empty:
        return pd.DataFrame(columns=EXAM_RESULTS_COLUMNS)
    
    mask = df["ChildName"] == child_name
    if exam_type:
        mask = mask & (df["ExamType"] == exam_type)
    
    result = df[mask].copy()
    if not result.empty:
        result = result.sort_values("ExamDate", ascending=False)
    return result


def get_child_exam_logs(child_name: str, exam_date: str = None, 
                        exam_type: str = None) -> pd.DataFrame:
    """Bir çocuğun sınav ders loglarını döndür."""
    df = get_exam_logs()
    if df.empty:
        return pd.DataFrame(columns=EXAM_LOGS_COLUMNS)
    
    mask = df["ChildName"] == child_name
    if exam_date:
        mask = mask & (df["ExamDate"] == exam_date)
    if exam_type:
        mask = mask & (df["ExamType"] == exam_type)
    
    result = df[mask].copy()
    if not result.empty:
        result = result.sort_values("ExamDate", ascending=False)
    return result
