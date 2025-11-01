import asyncio
import re
import json
import os
from pyrogram import Client, filters
from pyrogram.types import Message

# بيانات المستخدم
API_ID = 23933005
API_HASH = "cf389dadecdf3fac0aff0fb5c93f1f8b"
PHONE_NUMBER = "+201096200038"
SESSION_NAME = "price_analysis_session"

# ملف لتخزين بيانات الأسعار
PRICE_DATA_FILE = "price_data.json"
# ملف لتخزين قائمة القنوات المراد مراقبتها
CHANNELS_FILE = "monitored_channels.json"

# --------------------------------------------------------------------------------
# وظائف مساعدة
# --------------------------------------------------------------------------------

def load_monitored_channels() -> list:
    """تحميل قائمة القنوات المراد مراقبتها من ملف JSON."""
    if not os.path.exists(CHANNELS_FILE):
        return []
    try:
        with open(CHANNELS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_monitored_channels(channels: list):
    """حفظ قائمة القنوات المراد مراقبتها في ملف JSON."""
    with open(CHANNELS_FILE, 'w', encoding='utf-8') as f:
        json.dump(channels, f, ensure_ascii=False, indent=4)

def clean_text(text: str) -> str:
    """
    تنظيف النص من الإيموجي والرموز غير الضرورية.
    """
    # 1. إزالة الإيموجي
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F700-\U0001F77F"  # alchemical symbols
        "\U0001F780-\U0001F7FF"  # geometric shapes extended
        "\U0001F800-\U0001F8FF"  # supplemental arrows-c
        "\U0001F900-\U0001F9FF"  # supplemental symbols and pictographs
        "\U0001FA00-\U0001FA6F"  # chess symbols
        "\U0001FA70-\U0001FAFF"  # symbols and pictographs extended-a
        "\U00002702-\U000027B0"  # Dingbats
        "\U000024C2-\U0001F251" 
        "]+", flags=re.UNICODE
    )
    text = emoji_pattern.sub(r'', text)
    
    # 2. إزالة الرموز المتكررة وغير الأبجدية الرقمية (باستثناء الفواصل والنقاط وعلامات العملة)
    text = re.sub(r'[^\w\s\.\,\-\/:\u0600-\u06FF]+', ' ', text, flags=re.UNICODE)
    
    # 3. توحيد المسافات
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def extract_price_data(text: str) -> list:
    """
    استخراج بيانات الأسعار من النص المنظف.
    """
    prices = []
    
    # نمط للبحث عن الأرقام التي تسبقها أو تليها كلمات مثل "جنيه", "ج", "سعر", "ثمن"
    price_pattern = re.compile(
        r'(?:سعر|ثمن|جنيه|ج|شيكل|درهم|ريال)\s*(\d+(?:\.\d+)?)|(\d+(?:\.\d+)?)\s*(?:جنيه|ج|شيكل|درهم|ريال)',
        re.IGNORECASE | re.UNICODE
    )
    
    matches = price_pattern.findall(text)
    
    for match in matches:
        price = match[0] if match[0] else match[1]
        if price:
            prices.append(float(price))
            
    return prices

def save_price_data(data: dict):
    """تخزين البيانات المستخرجة في ملف JSON."""
    try:
        with open(PRICE_DATA_FILE, 'r', encoding='utf-8') as f:
            all_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        all_data = []
        
    all_data.append(data)
    
    with open(PRICE_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=4)

# --------------------------------------------------------------------------------
# معالجات الرسائل (Message Handlers)
# --------------------------------------------------------------------------------

app = Client(
    SESSION_NAME,
    api_id=API_ID,
    api_hash=API_HASH,
    phone_number=PHONE_NUMBER
)

# معرف الدردشة الخاص بالمستخدم (لإرسال الإشعارات)
USER_CHAT_ID = None

@app.on_message(filters.private & filters.me & filters.command("add_channel"))
async def add_channel_command(client: Client, message: Message):
    """إضافة قناة جديدة للمراقبة."""
    global USER_CHAT_ID
    USER_CHAT_ID = message.chat.id
    
    if len(message.command) < 2:
        await message.reply_text("الاستخدام: /add_channel [رابط أو اسم مستخدم القناة]")
        return
    
    channel_link = message.command[1]
    
    try:
        # الحصول على معلومات القناة
        chat = await client.get_chat(channel_link)
        
        monitored_channels = load_monitored_channels()
        
        # التحقق مما إذا كانت القناة مضافة بالفعل
        if chat.id in [c['id'] for c in monitored_channels]:
            await message.reply_text(f"القناة {chat.title} مضافة بالفعل للمراقبة.")
            return
            
        # إضافة القناة
        monitored_channels.append({
            "id": chat.id,
            "username": chat.username,
            "title": chat.title,
            "link": channel_link
        })
        save_monitored_channels(monitored_channels)
        
        await message.reply_text(f"تمت إضافة القناة **{chat.title}** بنجاح للمراقبة.")
        
    except Exception as e:
        await message.reply_text(f"حدث خطأ أثناء إضافة القناة: {e}")
        
@app.on_message(filters.private & filters.me & filters.command("list_channels"))
async def list_channels_command(client: Client, message: Message):
    """عرض قائمة القنوات التي تتم مراقبتها."""
    global USER_CHAT_ID
    USER_CHAT_ID = message.chat.id
    
    monitored_channels = load_monitored_channels()
    
    if not monitored_channels:
        await message.reply_text("لا توجد قنوات تتم مراقبتها حالياً.")
        return
        
    response = "قائمة القنوات التي تتم مراقبتها:\n"
    for i, channel in enumerate(monitored_channels):
        response += f"{i+1}. **{channel['title']}** (`{channel['id']}`)\n"
        
    await message.reply_text(response)

@app.on_message(filters.channel)
async def channel_message_handler(client: Client, message: Message):
    """يعالج الرسائل الواردة من القنوات ويستخرج الأسعار."""
    
    # التأكد من أن الرسالة نصية
    if not message.text:
        return
    
    monitored_channels = load_monitored_channels()
    
    # التحقق مما إذا كانت القناة هي إحدى القنوات المراد مراقبتها
    if message.chat.id not in [c['id'] for c in monitored_channels]:
        return
    
    # 1. تنظيف النص
    cleaned_text = clean_text(message.text)
    
    # 2. استخراج بيانات الأسعار
    extracted_prices = extract_price_data(cleaned_text)
    
    # 3. تخزين البيانات
    if extracted_prices:
        data_to_save = {
            "channel_id": message.chat.id,
            "channel_title": message.chat.title,
            "message_id": message.id,
            "date": message.date.isoformat(),
            "original_text": message.text,
            "cleaned_text": cleaned_text,
            "extracted_prices": extracted_prices
        }
        save_price_data(data_to_save)
        
        print(f"تم استخراج بيانات أسعار من القناة: {message.chat.title} - الأسعار: {extracted_prices}")
        
        # إرسال إشعار للمستخدم (اختياري)
        if USER_CHAT_ID:
            await client.send_message(
                USER_CHAT_ID,
                f"**تم رصد سعر جديد!**\n"
                f"القناة: {message.chat.title}\n"
                f"الأسعار المستخرجة: {extracted_prices}\n"
                f"النص الأصلي: {message.text[:100]}..."
            )

def main():
    """تشغيل العميل."""
    print("بدء تشغيل عميل تليجرام لمراقبة القنوات...")
    
    # تهيئة قائمة القنوات المبدئية (لأول مرة)
    if not os.path.exists(CHANNELS_FILE):
        # القنوات العامة التي تم تزويدي بها (سنضيفها يدوياً عبر الأمر /add_channel)
        # القنوات الخاصة لا يمكن إضافتها بالرابط مباشرة، يجب إضافتها يدوياً عبر الأمر /add_channel
        pass
        
    app.run()

if __name__ == "__main__":
    # تشغيل الوظيفة غير المتزامنة
    app.run()
