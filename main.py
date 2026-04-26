import streamlit as st
import yfinance as yf
import pandas as pd
from groq import Groq

st.set_page_config(page_title="AI Stock Analyzer", page_icon="⚡", layout="wide")

def local_css(file_name):
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except: pass

local_css("style.css")

def get_market_mood(hist_data):
    if len(hist_data) < 15: return "לא ידוע"
    delta = hist_data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    current_rsi = rsi.iloc[-1]
    
    if current_rsi > 70: return "קניות יתר (זהירות)"
    elif current_rsi < 30: return "מכירות יתר (הזדמנות?)"
    else: return "ניטרלי"

try:
    api_key = st.secrets["GROQ_API_KEY"]
except:
    st.error("שגיאה: חסר מפתח API של Groq ב-Secrets")
    st.stop()

st.title("⚡ מערכת האנליסטים שלך")
ticker = st.text_input("🔍 הכנס סימול מניה (למשל: NVDA, AAPL):").upper()

if st.button("בצע ניתוח מלא 🚀"):
    if ticker:
        with st.spinner("שואב נתונים ומנתח..."):
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                
                cp = info.get('currentPrice', info.get('regularMarketPrice', 'לא זמין'))
                high_target = info.get('targetHighPrice', 'לא זמין')
                low_target = info.get('targetLowPrice', 'לא זמין')
                mean_t = info.get('targetMeanPrice', 'לא זמין')
                beta = info.get('beta', 'לא זמין')
                
                hist_data = stock.history(period="3mo")
                market_mood = get_market_mood(hist_data)
                
                try:
                    financials = stock.quarterly_financials
                    latest_financials = financials.iloc[:, 0].to_dict() if not financials.empty else "לא זמין"
                except:
                    latest_financials = "לא זמין כרגע"
                    
                try:
                    news_list = stock.news[:3]
                except:
                    news_list = []
                
                st.subheader("🎯 מדדי מפתח")
                c1, c2, c3 = st.columns(3)
                
                # --- כאן הוספנו את ההסברים הקופצים (Tooltips) ---
                c1.metric("מחיר נוכחי", f"${cp}", help="המחיר האחרון שבו נסחרה המניה בוול-סטריט.")
                c2.metric("יעד ממוצע", f"${mean_t}", help="המחיר שאליו מעריכים האנליסטים שהמניה תגיע בשנה הקרובה.")
                c3.metric("בטא (Beta)", beta, help="מדד רמת הסיכון: בטא מעל 1 מצביעה על מניה תנודתית ומסוכנת יותר מהשוק. בטא מתחת ל-1 מצביעה על מניה יציבה יותר.")
                
                st.divider()
                
                client = Groq(api_key=api_key)
                
                # --- עדכנו את הפרומפט כדי שיחזיר תשובה מרוווחת עם נקודות ---
                prompt = f"""
                אתה אנליסט מומחה להשקעות. נתח את {ticker}.
                מחיר: {cp} | תחזיות: ממוצעת ({mean_t}).
                בטא: {beta} | מומנטום: {market_mood} | חדשות: {str(news_list)}
                
                החזר דוח מסודר, מרוווח וקריא מאוד, עם הכותרות הבאות. 
                חובה להשתמש בנקודות (Bullet points) בכל פסקה ולא לכתוב גושי טקסט ארוכים:
                
                ### 🏢 מה החברה עושה?
                * (הסבר קצר ותמציתי)
                
                ### 📊 קולות מוול-סטריט
                * (ניתוח תחזיות ומומנטום)
                
                ### 🚨 ניתוח סיכון
                * (התייחסות למדד הבטא ולסיכונים כלליים)
                
                ### 💡 השורה התחתונה
                * **ציון סנטימנט (1-10):** [מספר]
                * **ציון סיכון (1-10):** [מספר]
                * (משפט סיכום למשקיע)
                """
                
                chat_completion = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.3-70b-versatile",
                )
                
                st.subheader("🧠 ניתוח בינה מלאכותית")
                st.write(chat_completion.choices[0].message.content)
                
            except Exception as e:
                st.error(f"שגיאה: {e}")