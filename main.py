import streamlit as st
import yfinance as yf
import pandas as pd
from google import genai

st.set_page_config(page_title="AI Stock Analyzer", page_icon="⚡", layout="wide")

def local_css(file_name):
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except:
        pass

local_css("style.css")

def get_market_mood(hist_data):
    if len(hist_data) < 15:
        return "לא ידוע"
    delta = hist_data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    current_rsi = rsi.iloc[-1]
    
    if current_rsi > 70: return "קניות יתר (זהירות)"
    elif current_rsi < 30: return "מכירות יתר (הזדמנות?)"
    else: return "ניטרלי"

# --- משיכת המפתח מקובץ הסודות שיצרנו! ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except:
    st.error("שגיאה: לא נמצא מפתח API בקובץ הסודות.")
    st.stop()

st.title("⚡ מערכת האנליסטים שלך")
st.markdown("הזן סימול מניה וקבל ניתוח עומק מבוסס בינה מלאכותית, ללא צורך בהזנת מפתחות.")

# חיפוש מרכזי וגדול
ticker = st.text_input("🔍 הכנס סימול מניה (לדוגמה: AAPL, NVDA, DXYZ):").upper()

if st.button("בצע ניתוח מלא 🚀"):
    if not ticker:
        st.warning("אנא הכנס סימול מניה.")
    else:
        with st.spinner(f"סורק את הרשת ומנתח את {ticker}..."):
            try:
                client = genai.Client(api_key=api_key)
                stock = yf.Ticker(ticker)
                info = stock.info
                
                current_price = info.get('currentPrice', info.get('regularMarketPrice', 'לא זמין'))
                high_target = info.get('targetHighPrice', 'לא זמין')
                low_target = info.get('targetLowPrice', 'לא זמין')
                mean_target = info.get('targetMeanPrice', 'לא זמין')
                beta = info.get('beta', 'לא זמין')
                summary = info.get('longBusinessSummary', 'לא נמצא תיאור.')
                
                hist_data = stock.history(period="3mo")
                market_mood = get_market_mood(hist_data)
                financials = stock.quarterly_financials
                latest_financials = financials.iloc[:, 0].to_dict() if not financials.empty else "לא זמין"
                news_list = stock.news[:3]
                
                st.subheader("🎯 תחזיות וסיכונים")
                col1, col2, col3 = st.columns(3)
                col1.metric("מחיר נוכחי", f"${current_price}")
                col2.metric("תחזית וול-סטריט (ממוצע)", f"${mean_target}")
                col3.metric("מדד תנודתיות (Beta)", beta)
                
                st.divider()
                
                prompt = f"""
                אתה אנליסט מומחה להשקעות שמייעץ למשקיע. נתח את {ticker}.
                מחיר נוכחי: {current_price} | תחזיות: גבוהה ({high_target}), ממוצעת ({mean_target}), נמוכה ({low_target}).
                בטא: {beta} | מומנטום: {market_mood} | דוח: {latest_financials} | חדשות: {str(news_list)}
                
                החזר דוח מסודר עם הכותרות הבאות:
                ### 🏢 מה החברה עושה?
                ### 📊 קולות מוול-סטריט והדוחות
                ### 🚨 ניתוח סיכון
                ### 💡 השורה התחתונה (ציון סנטימנט: [1-10] | ציון סיכון: [1-10])
                """
                
                response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                
                st.subheader("🧠 ניתוח ה-AI")
                st.write(response.text)
                
            except Exception as e:
                st.error("אופס, אירעה שגיאה. נסה מניה אחרת.")