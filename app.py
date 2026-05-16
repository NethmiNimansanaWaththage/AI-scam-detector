from transformers import pipeline
import streamlit as st
import re
from datetime import datetime
import json
import os

# Page configuration
st.set_page_config(page_title="AI Scam Detector", page_icon="🛡️", layout="centered")

# Title
st.title("🛡️ AI Scam Detector")
st.markdown("*Paste any message to check if it's a scam, spam, or safe*")

# Load the AI model (cached for speed)
@st.cache_resource
def load_model():
    return pipeline("zero-shot-classification", 
                    model="facebook/bart-large-mnli")

# Load model
with st.spinner("Loading AI model... (first time takes 30 seconds)"):
    classifier = load_model()

# Labels for classification
labels = ["normal safe message", "spam advertisement", "scam fraud", "phishing link"]

# Function to extract suspicious elements
def extract_phone_numbers(text):
    pattern = r'(07\d{8}|0\d{9}|\+94\d{9})'
    return re.findall(pattern, text)

def extract_links(text):
    pattern = r'https?://[^\s]+|bit\.ly/[^\s]+|tinyurl\.com/[^\s]+'
    return re.findall(pattern, text)

# Function to save history
def save_to_history(message, prediction, confidence, phones, links):
    history_file = "scam_history.json"
    entry = {
        "timestamp": datetime.now().isoformat(),
        "message": message[:200],
        "prediction": prediction,
        "confidence": confidence,
        "phones": phones,
        "links": links
    }
    
    try:
        if os.path.exists(history_file):
            with open(history_file, "r") as f:
                history = json.load(f)
        else:
            history = []
    except:
        history = []
    
    history.append(entry)
    
    with open(history_file, "w") as f:
        json.dump(history, f, indent=2)

# Input area
user_input = st.text_area("📱 Enter message to analyze:", 
                           height=150,
                           placeholder="Paste an SMS, WhatsApp message, or email here...")

# Analyze button
if st.button("🔍 Detect Scam", type="primary"):
    if user_input:
        with st.spinner("Analyzing message..."):
            # Get AI prediction
            result = classifier(user_input, labels)
            prediction = result['labels'][0]
            confidence = result['scores'][0]
            
            # Extract suspicious elements
            phones = extract_phone_numbers(user_input)
            links = extract_links(user_input)
            
            # Save to history
            save_to_history(user_input, prediction, confidence, phones, links)
            
            # Show results
            st.divider()
            st.subheader("📊 Analysis Result")
            
            # Color-coded result
            if prediction in ["scam fraud", "phishing link"]:
                st.error(f"⚠️ {prediction.upper()} DETECTED")
                st.warning(f"Confidence: {confidence:.1%}")
                st.markdown("**🚨 Action advised:** Do not reply, click links, or call any numbers.")
                
            elif prediction == "spam advertisement":
                st.warning(f"📢 {prediction.upper()}")
                st.info(f"Confidence: {confidence:.1%}")
                st.markdown("**📌 Action advised:** Mark as spam and ignore.")
                
            else:
                st.success(f"✅ {prediction.upper()}")
                st.info(f"Confidence: {confidence:.1%}")
            
            # Show suspicious elements
            if phones:
                st.markdown("---")
                st.markdown("📞 **Suspicious phone numbers found:**")
                for phone in phones:
                    st.code(phone)
                st.caption("💡 Block these numbers if possible")
            
            if links:
                st.markdown("---")
                st.markdown("🔗 **Suspicious links found:**")
                for link in links:
                    st.code(link)
                st.caption("💡 Do NOT click - report to Google Safe Browsing")
            
            # Show full prediction breakdown
            with st.expander("🔍 View detailed analysis"):
                st.write("AI Confidence scores:")
                for label, score in zip(result['labels'], result['scores']):
                    st.progress(score, text=f"{label}: {score:.1%}")
                    
    else:
        st.warning("Please enter a message to analyze")

# Sidebar with info
with st.sidebar:
    st.markdown("## 🛡️ About")
    st.markdown("This AI detects scams, phishing, and spam in messages using state-of-the-art language models.")
    
    st.markdown("## 📊 Statistics")
    if os.path.exists("scam_history.json"):
        with open("scam_history.json", "r") as f:
            history = json.load(f)
        st.metric("Total messages analyzed", len(history))
        scam_count = sum(1 for h in history if h['prediction'] in ["scam fraud", "phishing link"])
        st.metric("Scams detected", scam_count)
    
    st.markdown("## 📝 Examples to try")
    st.markdown("**Scam example:**")
    st.code("Your Bank Alert: Account suspended. Verify now: http://fake-bank.com")
    st.markdown("**Spam example:**")
    st.code("CONGRATULATIONS! You won iPhone 15. Send 'WIN' to 77123")
    st.markdown("**Safe example:**")
    st.code("Hey, meeting at 3pm tomorrow? Don't forget the report.")

st.markdown("---")
st.caption("🔒 This AI runs locally — your messages are not stored on any external server (optional history is saved locally)")
