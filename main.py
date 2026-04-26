import streamlit as st
import yfinance as yf
import pandas as pd
from google import genai
from tenacity import retry, stop_after_attempt, wait_fixed

st.set_page_config(page_title="AI Stock Analyzer", page_icon="⚡", layout="wide")

# טעינת ה-CSS ששיפרנו
def local_css(file_name):
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except: pass

local_css("style.css")

# פונקציה עקשנית לפנייה ל-AI - תנסה 3 פעמים לפני שתתייאש
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def generate_ai_analysis(client, prompt):
    return client.models.generate_content(model='gemini-2.5-flash', contents=prompt)

try:
    api_key = st.secrets["GEMINI_API_KEY"]
except:
    st.error("שגיאה: חסר API Key ב-Secrets")
    st.stop()

st.title("⚡ מערכת האנליסטים שלך")

ticker = st.text_input("🔍 הכנס סימול מניה (למשל: NVDA):").upper()

if st.button("בצע ניתוח מלא 🚀"):
    if ticker:
        with st.spinner("מנתח נתונים..."):
            try:
                # משיכת נתונים מיאהו
                stock = yf.Ticker(ticker)
                info = stock.info
                
                # נתונים בסיסיים
                cp = info.get('currentPrice', 'לא זמין')
                mean_t = info.get('targetMeanPrice', 'לא זמין')
                beta = info.get('beta', 'לא זמין')
                
                st.subheader("🎯 מדדי מפתח")
                c1, c2, c3 = st.columns(3)
                c1.metric("מחיר", f"${cp}")
                c2.metric("יעד ממוצע", f"${mean_t}")
                c3.metric("בטא", beta)
                
                # פנייה ל-AI עם מנגנון ה-Retry
                client = genai.Client(api_key=api_key)
                prompt = f"נתח בקצרה את מניית {ticker}. מחיר: {cp}, בטא: {beta}. תן שורה תחתונה בעברית."
                
                response = generate_ai_analysis(client, prompt)
                
                st.subheader("🧠 ניתוח בינה מלאכותית")
                st.write(response.text)
                
            except Exception as e:
                if "Rate limited" in str(e) or "429" in str(e):
                    st.error("השרת של גוגל עמוס בגלל עומס משתמשים בענן. נסה שוב בעוד דקה, זה בדרך כלל מסתדר.")
                else:
                    st.error(f"שגיאה: {e}")