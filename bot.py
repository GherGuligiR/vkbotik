import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import sqlite3
import random
import time
import os

# =========================
# 🔐 ТОКЕН (вынесите в переменные окружения на Railway)
# =========================
TOKEN = os.getenv("VK_TOKEN", "vk1.a.J-XTxTnnLSZnNqqtW3BsCYtCmPyPP0BpHdbViegEZFpW6Hn5MpJMSzNb_ni-681NmQqMToUgje4w_dTWuSMofIhLDxMnve33UyT1yZgB1Kbhadwsvqg9YYRVOip-p2egeaqo4GQL7JXzMHD5SybTS_wtDQpEdsHvaQJE_i8NquZoLKNJedr1BXmQVrm8YRDR8zSKKvwB6a1Q0UTCJr92bQ")
ADMIN_ID = 492421638

# =========================
# 📦 SQLite
# =========================
conn = sqlite3.connect("dune.db", check_same_thread=False)
cursor = conn.cursor()

# =========================
# 🤖 VK
# =========================
vk = vk_api.VkApi(token=TOKEN)
longpoll = VkLongPoll(vk)
api = vk.get_api()

# =========================
# 📩 Сообщение
# =========================
def send_message(user_id, message, keyboard=None):
    api.messages.send(
        user_id=user_id,
        message=message,
        random_id=random.randint(1, 999999),
        keyboard=keyboard
    )

# =========================
# 🎮 КЛАВИАТУРЫ
# =========================
def main_keyboard(is_admin=False):
    kb = VkKeyboard()
    
    kb.add_button("🎮 Начать", VkKeyboardColor.POSITIVE)
    kb.add_button("📜 Меню", VkKeyboardColor.SECONDARY)
    kb.add_line()
    kb.add_button("🔄 Сбросить прогресс", VkKeyboardColor.NEGATIVE)
    
    if is_admin:
        kb.add_line()
        kb.add_button("👑 Админ панель", VkKeyboardColor.PRIMARY)
    
    return kb.get_keyboard()

def admin_keyboard():
    kb = VkKeyboard()
    
    kb.add_button("/all_scenes", VkKeyboardColor.PRIMARY)
    kb.add_button("/all_choice", VkKeyboardColor.PRIMARY)
    kb.add_line()
    kb.add_button("➕ Добавить сцену", VkKeyboardColor.POSITIVE)
    kb.add_button("❌ Удалить сцену", VkKeyboardColor.NEGATIVE)
    kb.add_line()
    kb.add_button("✏️ Редакт. сцену", VkKeyboardColor.SECONDARY)
    kb.add_button("📝 Добавить выбор", VkKeyboardColor.POSITIVE)
    kb.add_line()
    kb.add_button("🗑 Удалить выбор", VkKeyboardColor.NEGATIVE)
    kb.add_button("🔧 Редакт. выбор", VkKeyboardColor.SECONDARY)
    kb.add_line()
    kb.add_button("🔙 Назад", VkKeyboardColor.SECONDARY)
    
    return kb.get_keyboard()

def scene_keyboard(choices):
    kb = VkKeyboard()
    
    for idx, c in enumerate(choices, start=1):
        kb.add_button(f"{idx}. {c[1]}", VkKeyboardColor.PRIMARY)
        kb.add_line()
    
    kb.add_button("📜 Меню", VkKeyboardColor.SECONDARY)
    return kb.get_keyboard()

# =========================
# 👤 ИГРОК
# =========================
def get_player(user_id):
    cursor.execute("SELECT * FROM Players WHERE VkId=?", (user_id,))
    return cursor.fetchone()

def create_player(user_id):
    cursor.execute(
        "INSERT INTO Players (VkId, CurrentScene, Health, Water) VALUES (?, 'start', 100, 50)",
        (user_id,)
    )
    conn.commit()

def reset_player(user_id):
    cursor.execute("""
        UPDATE Players 
        SET CurrentScene='start', Health=100, Water=50, Karma=0
        WHERE VkId=?
    """, (user_id,))
    conn.commit()

def check_death(user_id):
    player = get_player(user_id)
    if player[2] <= 0 or player[3] <= 0:
        send_message(
            user_id,
            f"💀 ВЫ ПОГИБЛИ В ПУСТЫНЕ АРРАКИСА 💀\n\n❤️ Здоровье: {player[2]}\n💧 Вода: {player[3]}\n\nНажмите «Сбросить прогресс», чтобы начать заново.",
            main_keyboard(user_id == ADMIN_ID)
        )
        return True
    return False

# =========================
# 🎬 СЦЕНЫ
# =========================
def get_scene(scene):
    cursor.execute("SELECT Text FROM Scenes WHERE Scene=?", (scene,))
    r = cursor.fetchone()
    return r[0] if r else "Сцена не найдена"

def get_choices(scene):
    cursor.execute("SELECT Id, ChoiceText FROM Choices WHERE SceneId=?", (scene,))
    return cursor.fetchall()

def apply_choice(user_id, choice_id):
    cursor.execute("""
        SELECT NextScene, WaterEffect, HealthEffect, KarmaEffect 
        FROM Choices WHERE Id=?
    """, (choice_id,))
    
    r = cursor.fetchone()
    if not r:
        return False
    
    next_scene, water, health, karma = r
    
    cursor.execute("""
        UPDATE Players
        SET CurrentScene=?, Water=Water+?, Health=Health+?, Karma=Karma+?
        WHERE VkId=?
    """, (next_scene, water, health, karma, user_id))
    
    conn.commit()
    return True

def show_scene(user_id):
    player = get_player(user_id)
    
    if check_death(user_id):
        return
    
    scene = player[1]
    text = get_scene(scene)
    choices = get_choices(scene)
    
    # Если нет выборов — это концовка
    if not choices:
        msg = f"🏁 {text}\n\n"
        msg += f"❤️ {player[2]} | 💧 {player[3]} | ⚖️ Карма: {player[4]}\n\n"
        msg += "Нажмите «Сбросить прогресс», чтобы начать заново"
        send_message(user_id, msg, main_keyboard(user_id == ADMIN_ID))
        return
    
    msg = f"📖 {text}\n\n"
    
    for i, c in enumerate(choices, start=1):
        msg += f"{i}. {c[1]}\n"
    
    msg += f"\n❤️ {player[2]} | 💧 {player[3]} | ⚖️ Карма: {player[4]}"
    
    send_message(user_id, msg, scene_keyboard(choices))

# =========================
# 👑 АДМИН КОМАНДЫ
# =========================
def show_help(user_id):
    help_text = """
👑 АДМИН КОМАНДЫ 👑

📋 `/all_scenes` - показать все сцены с выборами
📊 `/all_choice` - показать все выборы

➕ Добавить сцену: `/add_scene (название) | (текст)`
❌ Удалить сцену: `/delete_scene (название)`

✏️ Редактировать сцену: `/edit_scene (название) | (новый текст)`

📝 Добавить выбор: `/add_choice (сцена) | (текст) | (след.сцена) | water(+/-число) | health(+/-число)`

🔧 Редактировать выбор: `/edit_choice (ID) | (сцена) | (текст) | (след.сцена) | water(+/-число) | health(+/-число)`

🗑 Удалить выбор: `/delete_choice (ID)`
"""
    send_message(user_id, help_text, admin_keyboard())

def show_all_scenes(user_id):
    cursor.execute("SELECT Scene, Text FROM Scenes")
    scenes = cursor.fetchall()
    
    msg = "📍 ВСЕ СЦЕНЫ 📍\n\n"
    
    for scene_name, scene_text in scenes:
        msg += f"🎬 {scene_name}\n📝 {scene_text[:100]}...\n"
        
        cursor.execute("SELECT ChoiceText, NextScene, WaterEffect, HealthEffect FROM Choices WHERE SceneId=?", (scene_name,))
        choices = cursor.fetchall()
        
        if choices:
            msg += "🔹 Выборы:\n"
            for c in choices:
                water = f"+{c[2]}" if c[2] >= 0 else str(c[2])
                health = f"+{c[3]}" if c[3] >= 0 else str(c[3])
                msg += f"  • {c[0]} → {c[1]} [💧{water} ❤️{health}]\n"
        else:
            msg += "  (нет выборов - концовка)\n"
        
        msg += "\n"
        if len(msg) > 3500:
            send_message(user_id, msg)
            msg = ""
    
    if msg:
        send_message(user_id, msg, admin_keyboard())

def show_all_choices(user_id):
    cursor.execute("SELECT Id, SceneId, ChoiceText, NextScene, WaterEffect, HealthEffect FROM Choices")
    choices = cursor.fetchall()
    
    msg = "📊 ВСЕ ВЫБОРЫ 📊\n\n"
    
    for c in choices:
        water = f"+{c[4]}" if c[4] >= 0 else str(c[4])
        health = f"+{c[5]}" if c[5] >= 0 else str(c[5])
        msg += f"🆔 ID: {c[0]}\n"
        msg += f"📍 Сцена: {c[1]}\n"
        msg += f"💬 Выбор: {c[2]}\n"
        msg += f"➡️ Следующая: {c[3]}\n"
        msg += f"💧 Вода: {water} | ❤️ Здоровье: {health}\n"
        msg += "─" * 20 + "\n"
    
    send_message(user_id, msg, admin_keyboard())

def add_scene(user_id, args):
    try:
        if "|" not in args:
            send_message(user_id, "❌ Формат: `/add_scene название | текст`")
            return
        scene_name, scene_text = args.split("|", 1)
        scene_name = scene_name.strip()
        scene_text = scene_text.strip()
        
        cursor.execute(
            "INSERT INTO Scenes (Scene, Text) VALUES (?, ?)",
            (scene_name, scene_text)
        )
        conn.commit()
        send_message(user_id, f"✅ Сцена {scene_name} добавлена!")
    except sqlite3.IntegrityError:
        send_message(user_id, f"❌ Сцена {scene_name} уже существует!")
    except Exception as e:
        send_message(user_id, f"❌ Ошибка: {e}")

def delete_scene(user_id, scene_name):
    scene_name = scene_name.strip()
    cursor.execute("DELETE FROM Choices WHERE SceneId=?", (scene_name,))
    cursor.execute("DELETE FROM Scenes WHERE Scene=?", (scene_name,))
    conn.commit()
    send_message(user_id, f"🗑 Сцена {scene_name} и все её выборы удалены!")

def edit_scene(user_id, args):
    try:
        if "|" not in args:
            send_message(user_id, "❌ Формат: `/edit_scene название | новый текст`")
            return
        scene_name, new_text = args.split("|", 1)
        scene_name = scene_name.strip()
        new_text = new_text.strip()
        
        cursor.execute("UPDATE Scenes SET Text=? WHERE Scene=?", (new_text, scene_name))
        conn.commit()
        
        if cursor.rowcount > 0:
            send_message(user_id, f"✅ Сцена {scene_name} обновлена!")
        else:
            send_message(user_id, f"❌ Сцена {scene_name} не найдена!")
    except Exception as e:
        send_message(user_id, f"❌ Ошибка: {e}")

def add_choice(user_id, args):
    try:
        parts = args.split("|")
        if len(parts) < 5:
            send_message(user_id, "❌ Формат: `/add_choice сцена | текст | след.сцена | water(+/-число) | health(+/-число)`")
            return
        
        scene_id = parts[0].strip()
        choice_text = parts[1].strip()
        next_scene = parts[2].strip()
        water = int(parts[3].strip())
        health = int(parts[4].strip())
        karma = int(parts[5].strip()) if len(parts) > 5 else 0
        
        cursor.execute("""
            INSERT INTO Choices (SceneId, ChoiceText, NextScene, WaterEffect, HealthEffect, KarmaEffect)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (scene_id, choice_text, next_scene, water, health, karma))
        conn.commit()
        
        send_message(user_id, f"✅ Выбор {choice_text} добавлен в сцену {scene_id}!")
    except Exception as e:
        send_message(user_id, f"❌ Ошибка: {e}")

def edit_choice(user_id, args):
    try:
        parts = args.split("|")
        if len(parts) < 6:
            send_message(user_id, "❌ Формат: `/edit_choice ID | сцена | текст | след.сцена | water(+/-число) | health(+/-число)`")
            return
        
        choice_id = int(parts[0].strip())
        scene_id = parts[1].strip()
        choice_text = parts[2].strip()
        next_scene = parts[3].strip()
        water = int(parts[4].strip())
        health = int(parts[5].strip())
        karma = int(parts[6].strip()) if len(parts) > 6 else 0
        
        cursor.execute("""
            UPDATE Choices 
            SET SceneId=?, ChoiceText=?, NextScene=?, WaterEffect=?, HealthEffect=?, KarmaEffect=?
            WHERE Id=?
        """, (scene_id, choice_text, next_scene, water, health, karma, choice_id))
        conn.commit()
        
        if cursor.rowcount > 0:
            send_message(user_id, f"✅ Выбор ID {choice_id} обновлён!")
        else:
            send_message(user_id, f"❌ Выбор ID {choice_id} не найден!")
    except Exception as e:
        send_message(user_id, f"❌ Ошибка: {e}")

def delete_choice(user_id, choice_id):
    try:
        choice_id = int(choice_id.strip())
        cursor.execute("DELETE FROM Choices WHERE Id=?", (choice_id,))
        conn.commit()
        
        if cursor.rowcount > 0:
            send_message(user_id, f"🗑 Выбор ID {choice_id} удалён!")
        else:
            send_message(user_id, f"❌ Выбор ID {choice_id} не найден!")
    except Exception as e:
        send_message(user_id, f"❌ Ошибка: {e}")

# =========================
# 🚀 ОСНОВНОЙ ЦИКЛ
# =========================
print("🤖 БОТ ЗАПУЩЕН...")

# Для защиты от дублирования сообщений
last_message_ids = set()

while True:
    try:
        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                
                # Защита от дублей
                if event.message_id in last_message_ids:
                    continue
                last_message_ids.add(event.message_id)
                if len(last_message_ids) > 100:
                    last_message_ids.clear()
                
                user_id = event.user_id
                raw_msg = event.text.strip()
                msg = raw_msg.lower()
                
                # Создание игрока
                player = get_player(user_id)
                if not player:
                    create_player(user_id)
                    welcome_msg = """🏜️ ДОБРО ПОЖАЛОВАТЬ НА АРРАКИС 🏜️

Ты прибыл на планету пустыни, где вода дороже золота, а песчаные черви правят подземным миром.

Как играть:
• Нажимай на кнопки с номерами вариантов
• Следи за 💧 водой и ❤️ здоровьем
• Твои решения влияют на судьбу

Команды:
🎮 Начать - продолжить игру
📜 Меню - показать команды
🔄 Сбросить прогресс - начать заново

Да прибудет с тобой вода! 💧"""
                    send_message(user_id, welcome_msg, main_keyboard(user_id == ADMIN_ID))
                    continue
                
                # ===== АДМИН КОМАНДЫ =====
                if user_id == ADMIN_ID:
                    # Обработка кнопок админ-панели
                    if raw_msg == "👑 Админ панель":
                        show_help(user_id)
                        continue
                    elif raw_msg == "🔙 Назад":
                        send_message(user_id, "Главное меню", main_keyboard(True))
                        continue
                    elif raw_msg == "➕ Добавить сцену":
                        send_message(user_id, "Введите: `/add_scene название | текст`")
                        continue
                    elif raw_msg == "❌ Удалить сцену":
                        send_message(user_id, "Введите: `/delete_scene название`")
                        continue
                    elif raw_msg == "✏️ Редакт. сцену":
                        send_message(user_id, "Введите: `/edit_scene название | новый текст`")
                        continue
                    elif raw_msg == "📝 Добавить выбор":
                        send_message(user_id, "Введите: `/add_choice сцена | текст | след.сцена | water(+/-число) | health(+/-число)`")
                        continue
                    elif raw_msg == "🔧 Редакт. выбор":
                        send_message(user_id, "Введите: `/edit_choice ID | сцена | текст | след.сцена | water(+/-число) | health(+/-число)`")
                        continue
                    elif raw_msg == "🗑 Удалить выбор":
                        send_message(user_id, "Введите: `/delete_choice ID`")
                        continue
                    
                    # Текстовые админ-команды
                    if msg == "/help":
                        show_help(user_id)
                        continue
                    elif msg == "/all_scenes":
                        show_all_scenes(user_id)
                        continue
                    elif msg == "/all_choice":
                        show_all_choices(user_id)
                        continue
                    elif msg.startswith("/add_scene"):
                        add_scene(user_id, raw_msg[11:])
                        continue
                    elif msg.startswith("/delete_scene"):
                        delete_scene(user_id, raw_msg[14:])
                        continue
                    elif msg.startswith("/edit_scene"):
                        edit_scene(user_id, raw_msg[12:])
                        continue
                    elif msg.startswith("/add_choice"):
                        add_choice(user_id, raw_msg[12:])
                        continue
                    elif msg.startswith("/edit_choice"):
                        edit_choice(user_id, raw_msg[13:])
                        continue
                    elif msg.startswith("/delete_choice"):
                        delete_choice(user_id, raw_msg[15:])
                        continue
                
                # ===== ИГРОК КОМАНДЫ =====
                if msg == "🎮 начать" or msg == "начать":
                    show_scene(user_id)
                    continue
                
                elif msg == "📜 меню" or msg == "меню":
                    menu_text = """📜 ДОСТУПНЫЕ КОМАНДЫ 📜

🎮 Начать - продолжить игру с последнего сохранения
🔄 Сбросить прогресс - начать игру заново
📜 Меню - показать это сообщение

Как играть:
Просто нажимай на кнопки с цифрами (1, 2, 3...)
Твои решения влияют на сюжет!

💡 *Совет: следи за водой и здоровьем!*"""
                    send_message(user_id, menu_text, main_keyboard(user_id == ADMIN_ID))
                    continue
                
                elif msg == "🔄 сбросить прогресс" or msg == "сбросить прогресс":
                    reset_player(user_id)
                    send_message(user_id, "🔄 Прогресс сброшен! Начни игру заново командой «Начать»", main_keyboard(user_id == ADMIN_ID))
                    continue
                
                # ===== ОБРАБОТКА ВЫБОРА =====
                else:
                    player = get_player(user_id)
                    if not player:
                        create_player(user_id)
                        show_scene(user_id)
                        continue
                    
                    choices = get_choices(player[1])
                    
                    # Если нет выборов (концовка) - не обрабатываем
                    if not choices:
                        send_message(user_id, "Игра окончена. Нажми «Сбросить прогресс», чтобы начать заново", main_keyboard(user_id == ADMIN_ID))
                        continue
                    
                    selected_id = None
                    
                    # По номеру (1, 2, 3...)
                    if msg.isdigit():
                        idx = int(msg) - 1
                        if 0 <= idx < len(choices):
                            selected_id = choices[idx][0]
                    
                    # По тексту кнопки (с учётом префикса "1. текст")
                    else:
                        for c in choices:
                            button_text = f"{choices.index(c)+1}. {c[1]}"
                            if raw_msg == button_text or raw_msg == c[1]:
                                selected_id = c[0]
                                break
                    
                    if selected_id:
                        apply_choice(user_id, selected_id)
                        show_scene(user_id)
                    else:
                        send_message(
                            user_id,
                            "🌪️ Буря засвистела меж вами, рассказчик не услышал вас...\n\nПовторите свой выбор или напишите «Меню»",
                            main_keyboard(user_id == ADMIN_ID)
                        )
    
    except Exception as e:
        print(f"Ошибка: {e}")
        time.sleep(3)
