import os
import requests
from flask import Flask, request
import google.generativeai as genai

app = Flask(__name__)

# --- CẤU HÌNH THÔNG SỐ (Thay các giá trị này vào) ---
FB_PAGE_ACCESS_TOKEN = 'DIEN_TOKEN_FACEBOOK_CUA_BAN'
FB_VERIFY_TOKEN = 'hieu_ghe_massage_2024' # Bạn tự đặt gì cũng được, nhưng phải khớp với FB Developer
GEMINI_API_KEY = 'DIEN_API_KEY_GEMINI_CUA_BAN'
TELEGRAM_BOT_TOKEN = 'DIEN_TOKEN_TELEGRAM_BOT'
TELEGRAM_CHAT_ID = 'DIEN_ID_TELEGRAM_CUA_BAN'

# --- CẤU HÌNH BỘ NÃO GEMINI ---
genai.configure(api_key=GEMINI_API_KEY)
SYSTEM_INSTRUCTION = """
Bạn là Trợ lý bán hàng thông minh cho cửa hàng ghế massage của Hiếu tại Thanh Hóa.
Nhiệm vụ: Tư vấn nhiệt tình, tập trung vào nỗi đau khách hàng (đau lưng, mỏi vai gáy, mất ngủ).
Kiến thức đặc thù cần lồng ghép:
1. Ghế có khung chống chuột và côn trùng (tránh hỏng mạch điện).
2. Con lăn Silicon đúc đặc (êm ái, bền hơn con lăn nhựa bọc cao su).
3. Động cơ bọc gang (chạy bền, tản nhiệt tốt).
Phong cách: Giọng miền Bắc, thân thiện, không dùng từ ngữ chuyên môn quá khó hiểu.
Mục tiêu: Nếu khách hỏi giá hoặc tư vấn sâu, hãy khéo léo xin Số Điện Thoại để nhân viên gọi lại báo giá ưu đãi.
"""

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=SYSTEM_INSTRUCTION
)

# --- CÁC HÀM XỬ LÝ ---

def send_fb_message(recipient_id, text):
    """Gửi tin nhắn trả lời khách trên Facebook"""
    url = f"https://graph.facebook.com/v19.0/me/messages?access_token={FB_PAGE_ACCESS_TOKEN}"
    payload = {"recipient": {"id": recipient_id}, "message": {"text": text}}
    requests.post(url, json=payload)

def send_telegram_alert(customer_msg, ai_reply):
    """Báo cáo về Telegram cho Hiếu"""
    text = f"🔔 **CÓ KHÁCH MỚI!**\n\n💬 Khách: {customer_msg}\n\n🤖 AI trả lời: {ai_reply}"
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"})

# --- WEBHOOK CHO FACEBOOK ---

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    # Bước xác minh Webhook với Facebook (chỉ chạy 1 lần đầu)
    if request.method == 'GET':
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        if mode == 'subscribe' and token == FB_VERIFY_TOKEN:
            return challenge, 200
        return 'Xác minh thất bại', 403

    # Xử lý tin nhắn đến
    data = request.json
    if data.get('object') == 'page':
        for entry in data['entry']:
            for messaging_event in entry.get('messaging', []):
                if messaging_event.get('message') and not messaging_event['message'].get('is_echo'):
                    sender_id = messaging_event['sender']['id']
                    user_text = messaging_event['message'].get('text')

                    if user_text:
                        # 1. Gọi Gemini xử lý
                        chat = model.start_chat()
                        response = chat.send_message(user_text)
                        ai_reply = response.text

                        # 2. Trả lời khách trên Messenger
                        send_fb_message(sender_id, ai_reply)

                        # 3. Thông báo cho chủ shop qua Telegram
                        send_telegram_alert(user_text, ai_reply)

    return 'OK', 200

if __name__ == '__main__':
    app.run(port=5000)
