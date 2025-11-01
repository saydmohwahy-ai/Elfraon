import asyncio
from pyrogram import Client

# بيانات المستخدم التي تم تزويدي بها
API_ID = 23933005
API_HASH = "cf389dadecdf3fac0aff0fb5c93f1f8b"
PHONE_NUMBER = "+201096200038"

# اسم الجلسة (يمكن أن يكون أي شيء)
SESSION_NAME = "price_analysis_session"

async def main():
    """وظيفة تسجيل الدخول إلى حساب المستخدم."""
    print("بدء عملية تسجيل الدخول...")
    
    # إنشاء عميل Pyrogram
    app = Client(
        SESSION_NAME,
        api_id=API_ID,
        api_hash=API_HASH,
        phone_number=PHONE_NUMBER
    )
    
    try:
        # بدء العميل
        await app.start()
        print("تم تسجيل الدخول بنجاح!")
        
        # يمكنك هنا طباعة معلومات الحساب للتأكد
        me = await app.get_me()
        print(f"مرحباً بك، {me.first_name} (@{me.username})")
        
        # إيقاف العميل
        await app.stop()
        
    except Exception as e:
        print(f"حدث خطأ أثناء تسجيل الدخول: {e}")
        print("يرجى التأكد من أنك لم تقم بتسجيل الدخول من مكان آخر وأنك مستعد لإرسال رمز المصادقة.")

if __name__ == "__main__":
    # تشغيل الوظيفة غير المتزامنة
    asyncio.run(main())
