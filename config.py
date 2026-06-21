"""
config.py — Study Tracker sabitler ve yapılandırma
"""

# ─── Çocuk İsimleri ───────────────────────────────────────────
CHILDREN = ["Ayşe Bade", "Elmas"]

# ─── Gün İsimleri (Pazartesi=0 ... Pazar=6) ──────────────────
DAY_NAMES = {
    0: "Pazartesi",
    1: "Salı",
    2: "Çarşamba",
    3: "Perşembe",
    4: "Cuma",
    5: "Cumartesi",
    6: "Pazar",
}

DAY_NAMES_SHORT = {
    0: "Pzt",
    1: "Sal",
    2: "Çar",
    3: "Per",
    4: "Cum",
    5: "Cmt",
    6: "Paz",
}

# ─── Renkler ──────────────────────────────────────────────────
COLORS = {
    "success": "#22c55e",       # yeşil — hedef tamamlandı
    "warning": "#f59e0b",       # sarı  — yaklaşıyor
    "danger":  "#ef4444",       # kırmızı — geride
    "info":    "#3b82f6",       # mavi  — bilgi
    "bg_card": "#1e1e2e",       # kart arka plan
    "text":    "#e2e8f0",       # metin rengi
}

# ─── Renk Paleti (grafikler için) ─────────────────────────────
CHART_COLORS = [
    "#3b82f6",  # mavi
    "#ef4444",  # kırmızı
    "#22c55e",  # yeşil
    "#f59e0b",  # sarı
    "#8b5cf6",  # mor
    "#ec4899",  # pembe
    "#14b8a6",  # teal
    "#f97316",  # turuncu
]

# ─── Türkiye Saat Dilimi ──────────────────────────────────────
TR_TZ = "Europe/Istanbul"

# ─── Google Sheets Sayfa İsimleri ─────────────────────────────
SHEET_LOGS        = "logs"
SHEET_TARGETS     = "targets"
SHEET_SUBJECTS    = "subjects"
SHEET_HOLIDAYS    = "holidays"
SHEET_EXAM_LOGS   = "exam_logs"
SHEET_EXAM_RESULTS = "exam_results"

SHEET_NAMES = [SHEET_LOGS, SHEET_TARGETS, SHEET_SUBJECTS, SHEET_HOLIDAYS,
               SHEET_EXAM_LOGS, SHEET_EXAM_RESULTS]

# ─── Sheet Başlıkları ─────────────────────────────────────────
LOGS_COLUMNS        = ["Date", "ChildName", "Subject", "Solved", "Incorrect", "Blank"]
TARGETS_COLUMNS     = ["ChildName", "Subject", "DayOfWeek", "TargetCount"]
SUBJECTS_COLUMNS    = ["ChildName", "Subject"]
HOLIDAYS_COLUMNS    = ["Date", "Reason"]
EXAM_LOGS_COLUMNS   = ["ExamDate", "ExamName", "ChildName", "ExamType", "Subject", "Correct", "Incorrect", "Blank", "Net"]
EXAM_RESULTS_COLUMNS = ["ExamDate", "ChildName", "ExamType", "Score", "Rank"]

# ─── Sınav Standartları (LGS) ──────────────────────────────────
EXAM_TYPES = ["LGS"]

EXAM_STANDARDS = {
    "LGS": [
        {"Subject": "Matematik", "TotalQuestions": 20},
        {"Subject": "Fen Bilgisi", "TotalQuestions": 20},
        {"Subject": "Türkçe", "TotalQuestions": 20},
        {"Subject": "İnkılap", "TotalQuestions": 10},
        {"Subject": "Din Kültürü", "TotalQuestions": 10},
        {"Subject": "İngilizce", "TotalQuestions": 10},
    ],
}

# ─── Emoji'ler ────────────────────────────────────────────────
EMOJI = {
    "success":  "✅",
    "warning":  "⚠️",
    "danger":   "❌",
    "fire":     "🔥",
    "target":   "🎯",
    "chart":    "📊",
    "calendar": "📅",
    "pencil":   "✏️",
    "save":     "💾",
    "delete":   "🗑️",
    "add":      "➕",
    "holiday":  "🏖️",
    "star":     "⭐",
    "trophy":   "🏆",
    "book":     "📚",
    "plan":     "📋",
}
