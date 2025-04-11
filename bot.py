import re
import gspread
import json
import os

from telegram import Update
from datetime import datetime

from oauth2client.service_account import ServiceAccountCredentials
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

# Kết nối Google Sheets
scope = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

if "GOOGLE_CREDS_JSON" not in os.environ:
    with open("credentials.json") as f:
        os.environ["GOOGLE_CREDS_JSON"] = f.read()

creds_dict = json.loads(os.environ["GOOGLE_CREDS_JSON"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)

client = gspread.authorize(creds)

sheet = client.open("Work Performance").sheet1  # Tên Sheet

# Token bot Telegram
TOKEN = "7969806613:AAG03Moin58c0_CixWvlnC_yhAGbWG74XFs"

def is_within_active_hours():
    now = datetime.now().hour
    return 8 <= now < 21  # hoạt động từ 08:00 đến 19:59

async def log_to_sheet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    user = update.effective_user
    message = update.message
    chat = update.effective_chat
    raw_text = message.text.strip()

    # 🔒 Kiểm tra giờ hoạt động
    if not is_within_active_hours():
        await update.message.reply_text("Ngoài giờ làm việc rồi nha! Bot chỉ hoạt động từ 08:00 đến 20:00.")
        return
    
    ma_phieu = ''
    thoigian_hoanthanh = ''

    try:
        today = datetime.now()
        short_year = today.strftime('%y')
        month_day = today.strftime('%m%d')

        parts = raw_text.split()

        if len(parts) == 2:
            first, second = parts

            # Trường hợp: CS286-YYMMDDxxxx yy
            if re.match(r"^CS\d+-\d+\w*$", first):
                ma_phieu = first
                thoigian_hoanthanh = second
            elif re.match(r"^[a-zA-Z0-9]+$", first):
                # Trường hợp: xxxx yy
                ma_phieu = f"CS286-{short_year}{month_day}{first}"
                thoigian_hoanthanh = second
            else:
                raise ValueError("Sai định dạng rồi nha! nhập lại!")

        elif len(parts) == 1:
            only = parts[0]

            # Trường hợp: CS286-YYMMDDxxxx
            if re.match(r"^CS\d+-\d+\w*$", only):
                ma_phieu = only
                thoigian_hoanthanh = ''

            elif re.match(r"^[a-zA-Z0-9]+$", only):
                # Trường hợp: xxxx
                ma_phieu = f"CS286-{short_year}{month_day}{only}"
                thoigian_hoanthanh = ''
            else:
                raise ValueError("Sai định dạng rồi nha! nhập lại!")

        else:
            raise ValueError("Sai định dạng rồi nha! nhập lại!")


        data = [
            datetime.now().strftime('%d-%m-%Y %H:%M:%S'),
            ma_phieu,
            user.full_name,
            None,
            thoigian_hoanthanh,
            '',
        ]

        sheet.append_row(data)
        await update.message.reply_text("note rồi nha " + user.full_name)

    except Exception as e:
        await update.message.reply_text(
            "Lỗi định dạng rồi nha, phải là 1 trong 4 dạng sau:\n"
            "- xxxx\n"
            "- xxxx yy\n"
            "- CS286-YYMMDDxxxx\n"
            "- CS286-YYMMDDxxxx yy"
        )

async def ignore_non_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return;

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT & (~filters.ChatType.PRIVATE), log_to_sheet))
app.add_handler(MessageHandler(~filters.TEXT, ignore_non_text))

print("Bot đang chạy...")
app.run_polling()

