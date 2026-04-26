import streamlit as st
import yfinance as yf
import pandas as pd
from groq import Groq

# הגדרות עמוד ועיצוב בסיסי
st.set_page_config(page_title="StockAI Premium", page_icon="⚡", layout="wide")

# טעינת העיצוב מה-CSS
def local_css():
    css = """
    @import url('https://fonts.googleapis.com/css2?family=Assistant:wght@300;400;700;800&display=swap');
    
    html, body, [class*="st-"], [data-testid="stAppViewContainer"] {
        direction: rtl; text-align: right; font-family: 'Assistant', sans-serif !important;
    }
    h1, h2, h3 { color: #2962FF !important; font-weight: 800 !important; }
    
    [data-testid="stMetric"] {
        background-color: #1E2130; padding: 15px; border-radius: 12px;
        border-right: 5px solid #2962FF; box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }
    
    .stMarkdown {
        background-color: #161B22; padding: 25px; border-radius: 15px;
        border: 1px solid #30363D; line-height: 1.8; font-size: 1.1rem;
    }
    
    .stMarkdown ul { padding-right: 20px !important; margin-right: 0px !important; }
    .stMarkdown li { margin-bottom: 8px; }
    
    .stButton button {
        background: linear-gradient(90deg, #2962FF 0%, #00C853 100%) !important;
        color: white !important; border: none !important; border-radius: 20px !important;
        width: 100%; font-weight: bold !important; padding: 12px !important; font-size: 1.2rem !important;
        box-shadow: 0 4px 15px rgba(41, 98, 255, 0.3) !important;
    }
    
    [data-testid="stChart"] { background-color: #1E2130; border-radius: 15px; padding: 10px; }
    """
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

local_css()

# פונקציית עזר לחישוב מומנטום
def get_market_mood(hist_data):
    if len(hist_data) < 15: return "ניטרלי"
    delta = hist_data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    curr = rsi.iloc[-1]
    if curr > 70: return "קניות יתר (זהירות)"
    elif curr < 30: return "מכירות יתר (הזדמנות)"
    return "ניטרלי"

# אימות מפתח API
try:
    api_key = st.secrets["GROQ_API_KEY"]
except:
    st.error("שגיאה: חסר מפתח API של Groq ב-Secrets")
    st.stop()

st.title("⚡ מערכת האנליסטים המקצועית")
ticker = st.text_input("🔍 הכנס סימול מניה (לדוגמה: NVDA, TSLA, MSFT):").upper()

if st.button("בצע ניתוח עומק 🚀"):
    if not ticker:
        st.warning("אנא הכנס סימול מניה.")
    else:
        with st.spinner(f"שואב נתונים ומכין ניתוח עבור {ticker}..."):
            try:
                # משיכת נתונים
                stock = yf.Ticker(ticker)
                info = stock.info
                
                st.header(f"{info.get('longName', ticker)}")
                
                # --- חלק 1: גרף אינטראקטיבי (שנה קבועה עם זום חופשי) ---
                st.subheader("📈 גרף מחיר (שנה אחרונה - גלול עם העכבר/אצבעות לזום)")
                hist = stock.history(period="1y")
                st.line_chart(hist['Close'], color="#2962FF")

                # --- חלק 2: מדדי מפתח ---
                st.subheader("🎯 נתונים פיננסיים")
                cp = info.get('currentPrice', info.get('regularMarketPrice', 'N/A'))
                target = info.get('targetMeanPrice', 'N/A')
                beta = info.get('beta', 'N/A')
                m_cap = info.get('marketCap', 0)
                pe = info.get('trailingPE', 'N/A')
                
                c1, c2, c3 = st.columns(3)
                c1.metric("מחיר נוכחי", f"${cp}")
                c2.metric("מחיר יעד (אנליסטים)", f"${target}")
                c3.metric("בטא (Beta)", beta)
                
                c4, c5, c6 = st.columns(3)
                c4.metric("שווי שוק", f"${m_cap:,.0f}" if isinstance(m_cap, (int, float)) else "N/A")
                c5.metric("מכפיל רווח (P/E)", pe)
                c6.metric("מומנטום", get_market_mood(hist))

                st.divider()

                # --- חלק 3: ניתוח ה-AI החכם ---
                st.subheader("🧠 דוח משקיעים (Powered by AI)")
                
                client = Groq(api_key=api_key)
                
                # שאיבת החדשות ותיאור החברה כדי שה-AI יקרא ויסכם הכל בעצמו
                company_desc = info.get('longBusinessSummary', 'אין מידע זמין.')
                try:
                    news_data = stock.news[:3] if stock.news else []
                except:
                    news_data = []

                prompt = f"""
                אתה אנליסט מומחה. המשתמש מחפש ניתוח קצר, קולע ומקצועי בעברית למניית {ticker}.
                נתונים: מחיר {cp}, מכפיל {pe}, בטא {beta}.
                פרופיל חברה באנגלית (תרגם ותמצת לעברית קלה): {company_desc}
                חדשות: {str(news_data)}
                
                החזר את הניתוח בדיוק לפי המבנה הזה:
                
                ### 🏢 תעודת זהות
                (תמצת את תיאור החברה לעברית ב-2 משפטים קצרים. בלי לחפור).
                
                ### 🟢 פוטנציאל וצמיחה (Bull Case)
                (2-3 סיבות לקנות. חובה להתחיל כל נקודה ב-🟢)
                
                ### 🔴 סיכונים מרכזיים (Bear Case)
                (2-3 סיכונים וממה להיזהר. חובה להתחיל כל נקודה ב-🔴)
                
                ### 💡 השורה התחתונה
                **ציון סנטימנט (1-10):** [מספר]
                **רמת סיכון (1-10):** [מספר]
                **המלצה מעשית למשקיע:** (משפט ברור ומודגש שממליץ האם זה זמן טוב לקנות, להמתין, או שזה גבולי כרגע בהתבסס על הנתונים).
                """
                
                chat = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.3-70b-versatile",
                )
                
                st.markdown(chat.choices[0].message.content)

            except Exception as e:
                st.error("אירעה שגיאה בטעינת המניה. ודא שהסימול תקין (למשל AAPL ולא אפל) ונסה שוב.")