import requests
import google.generativeai as genai
from flask import Flask, request

app = Flask(__name__)

# --- CẤU HÌNH ---
MY_VERIFY_TOKEN = "hieu_massage_2026"
FB_PAGE_ACCESS_TOKEN = "ĐIỀN_TOKEN_TRANG_CỦA_BẠN"
GEMINI_API_KEY = "ĐIỀN_API_KEY_GEMINI"
TELEGRAM_BOT_TOKEN = "ĐIỀN_TOKEN_BOT_TELEGRAM"
TELEGRAM_CHAT_ID = "ID_CỦA_BẠN"

# Cấu hình AI chuyên gia ghế massage
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction="Bạn là chuyên gia tư vấn ghế massage tại Thanh Hóa. Tập trung vào nỗi đau khách hàng, nhắc đến động cơ bọc gang và con lăn silicon. Khéo léo xin SĐT."
)

@app.route('/webhook', methods=['GET'])
def verify():
    if request.args.get("hub.verify_token") == MY_VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return "Mã xác minh không khớp!", 403

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    if data.get("object") == "page":
        for entry in data["entry"]:
            for messaging_event in entry.get("messaging", []):
                if messaging_event.get("message") and not messaging_event["message"].get("is_echo"):
                    sender_id = messaging_event["sender"]["id"]
                    user_text = messaging_event["message"].get("text")

                    # Gọi Gemini xử lý
                    response = model.generate_content(user_text)
                    ai_reply = response.text

                    # Gửi câu trả lời lại cho khách trên Fanpage
                    send_fb_message(sender_id, ai_reply)
                    
                    # Báo về Telegram cho Hiếu
                    requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", 
                                  json={"chat_id": TELEGRAM_CHAT_ID, "text": f"Khách: {user_text}\nAI: {ai_reply}"})

    return "EVENT_RECEIVED", 200

def send_fb_message(recipient_id, text):
    url = f"https://graph.facebook.com/v19.0/me/messages?access_token={FB_PAGE_ACCESS_TOKEN}"
    requests.post(url, json={"recipient": {"id": recipient_id}, "message": {"text": text}})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
