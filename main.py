import streamlit as st
import yfinance as yf
import pandas as pd
from groq import Groq

st.set_page_config(page_title="AI Stock Analyzer", page_icon="⚡", layout="wide")

# טעינת העיצוב שלנו
def local_css(file_name):
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except: pass

local_css("style.css")

# משיכת המפתח החדש מהסודות
try:
    api_key = st.secrets["GROQ_API_KEY"]
except:
    st.error("שגיאה: חסר מפתח API של Groq ב-Secrets")
    st.stop()

st.title("⚡ מערכת האנליסטים שלך")
ticker = st.text_input("🔍 הכנס סימול מניה (למשל: NVDA, AAPL):").upper()

if st.button("בצע ניתוח מלא 🚀"):
    if ticker:
        with st.spinner("שואב נתונים מיאהו ומנתח במהירות שיא..."):
            try:
                # משיכת נתונים מיאהו
                stock = yf.Ticker(ticker)
                info = stock.info
                
                cp = info.get('currentPrice', 'לא זמין')
                mean_t = info.get('targetMeanPrice', 'לא זמין')
                beta = info.get('beta', 'לא זמין')
                
                st.subheader("🎯 מדדי מפתח")
                c1, c2, c3 = st.columns(3)
                c1.metric("מחיר נוכחי", f"${cp}")
                c2.metric("יעד ממוצע", f"${mean_t}")
                c3.metric("בטא", beta)
                
                # פנייה ל-Groq AI (מודל Llama 3 70B)
                client = Groq(api_key=api_key)
                prompt = f"""
                אתה אנליסט מומחה. נתח את מניית {ticker}. 
                מחיר נוכחי: {cp}, בטא: {beta}.
                כתוב דוח קצר, מקצועי וברור הכולל:
                1. מה החברה עושה במשפט.
                2. סיכונים וסיכויים.
                3. שורה תחתונה למשקיע.
                * חשוב מאוד: ענה אך ורק בשפה העברית.
                """
                
                chat_completion = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama3-70b-8192",
                )
                
                st.subheader("🧠 ניתוח בינה מלאכותית (Powered by Llama-3)")
                st.write(chat_completion.choices[0].message.content)
                
            except Exception as e:
                st.error(f"שגיאה: {e}")