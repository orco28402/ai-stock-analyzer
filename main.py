import streamlit as st
import yfinance as yf
import pandas as pd
from groq import Groq

# הגדרות עמוד ועיצוב בסיסי
st.set_page_config(page_title="StockAI Premium", page_icon="⚡", layout="wide")

# טעינת העיצוב מה-CSS
def local_css(file_name):
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except: pass

local_css("style.css")

# פונקציית עזר לחישוב מומנטום (RSI)
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
        with st.spinner(f"סורק נתונים עבור {ticker}..."):
            try:
                # משיכת נתונים
                stock = yf.Ticker(ticker)
                info = stock.info
                
                # כותרת עם שם החברה המלא
                st.header(f"{info.get('longName', ticker)}")
                
                # --- חלק 1: גרף אינטראקטיבי ---
                st.subheader("📈 גרף מחיר היסטורי")
                time_range = st.select_slider(
                    "בחר טווח זמן:",
                    options=["שבוע", "חודש", "3 חודשים", "חצי שנה", "שנה"],
                    value="3 חודשים"
                )
                range_map = {"שבוע": "5d", "חודש": "1mo", "3 חודשים": "3mo", "חצי שנה": "6mo", "שנה": "1y"}
                hist = stock.history(period=range_map[time_range])
                st.line_chart(hist['Close'], color="#2962FF")

                # --- חלק 2: מדדי מפתח ---
                st.subheader("🎯 נתונים פיננסיים")
                cp = info.get('currentPrice', info.get('regularMarketPrice', 'N/A'))
                target = info.get('targetMeanPrice', 'N/A')
                beta = info.get('beta', 'N/A')
                m_cap = info.get('marketCap', 0)
                pe = info.get('trailingPE', 'N/A')
                
                c1, c2, c3 = st.columns(3)
                c1.metric("מחיר נוכחי", f"${cp}", help="המחיר האחרון של המניה בשוק.")
                c2.metric("מחיר יעד (אנליסטים)", f"${target}", help="ממוצע התחזיות של אנליסטים בוול-סטריט לשנה הקרובה.")
                c3.metric("בטא (Beta)", beta, help="מדד תנודתיות: מעל 1 נחשב מסוכן מהשוק, מתחת ל-1 יציב יותר.")
                
                c4, c5, c6 = st.columns(3)
                c4.metric("שווי שוק", f"${m_cap:,.0f}" if isinstance(m_cap, (int, float)) else "N/A", help="הערך הכולל של החברה בבורסה.")
                c5.metric("מכפיל רווח (P/E)", pe, help="כמה השוק מוכן לשלם על כל דולר של רווח.")
                c6.metric("מומנטום", get_market_mood(hist))

                st.divider()

                # --- חלק 3: טאבים ---
                t_ai, t_news, t_profile = st.tabs(["🧠 ניתוח AI עמוק", "📰 חדשות חמות", "🏢 אודות החברה"])

                with t_ai:
                    client = Groq(api_key=api_key)
                    prompt = f"נתח את מניית {ticker}. נתונים: מחיר {cp}, מכפיל {pe}, בטא {beta}. החזר דוח בעברית מסודר עם נקודות: ### 🏢 תמצית הפעילות ### 📈 פוטנציאל וצמיחה (Bull Case) ### ⚠️ סיכונים מרכזיים (Bear Case) ### 💡 סיכום וציונים - סנטימנט (1-10): [ציון] - רמת סיכון (1-10): [ציון]"
                    
                    chat = client.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model="llama-3.3-70b-versatile",
                    )
                    st.markdown(chat.choices[0].message.content)

                with t_news:
                    st.subheader("כותרות אחרונות מהשוק")
                    news = stock.news
                    if news:
                        for item in news[:5]:
                            st.markdown(f"🔗 **[{item['title']}]({item['link']})**")
                            # כאן התיקון - השתמשתי בגרש בודד לעטוף את הטקסט כדי שלא יתנגש עם ע"י
                            st.caption(f'פורסם ע"י: {item.get("publisher", "Unknown")}')
                            st.write("---")
                    else:
                        st.info("אין חדשות זמינות כרגע.")

                with t_profile:
                    st.subheader("כרטיס ביקור")
                    st.write(f"**סקטור:** {info.get('sector', 'N/A')}")
                    st.write(f"**תעשייה:** {info.get('industry', 'N/A')}")
                    if isinstance(info.get('fullTimeEmployees'), int):
                        st.write(f"**עובדים:** {info.get('fullTimeEmployees'):,}")
                    st.write(f"**תיאור:** {info.get('longBusinessSummary', 'אין תיאור זמין.')}")

            except Exception as e:
                st.error(f"אירעה שגיאה בשליפת הנתונים: {e}")