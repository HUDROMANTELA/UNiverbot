import aiosqlite
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
import datetime


API_TOKEN = 'API'
ADMIN_ID = ["ВАШИ АДМИНЫ ВВОД ЧИСЛАМИ"]  

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

async def send_long_message(message, text):
    chunk_size = 4096  
    for i in range(0, len(text), chunk_size):
        await message.answer(text[i:i + chunk_size])

def get_day_name(day_index):
    days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    return days[day_index]

async def get_schedule_by_day(day, db):
    async with db.execute("SELECT DISTINCT subject, time, room, building FROM schedule WHERE day = ? AND type_week IN (?, 'общ')", (day, current_week_type)) as cursor:
        return await cursor.fetchall()
    
current_week_type = "неч" 

async def init_db():
    async with aiosqlite.connect("university.db") as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS schedule (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            subject TEXT,
                            day TEXT,
                            time TEXT,
                            type_week TEXT,  -- 'чет', 'неч', 'общ'
                            room TEXT,
                            building TEXT)''')
        await db.execute('''CREATE TABLE IF NOT EXISTS homework (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            subject TEXT,
                            task TEXT,
                            due_date TEXT)''')
        await db.execute('''CREATE TABLE IF NOT EXISTS events (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            event_name TEXT,
                            event_date TEXT,
                            location TEXT)''')
        await db.execute('''CREATE TABLE IF NOT EXISTS materials (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            subject TEXT,
                            material TEXT)''')
        schedule_data = [
            ('История России', 'Понедельник', '08:00', 'общ', '513', '2зд'),
            ('Высшая математика', 'Понедельник', '09:40', 'общ', '334', '8зд'),
            ('Физика (спецкурс)', 'Понедельник', '11:20', 'общ', '334', '8зд'),
            ('Физика', 'Понедельник', '13:30', 'неч', '303', '2зд'),
            ('Физика', 'Вторник', '08:00', 'общ', '334', '8зд'),
            ('Основы российской государственности', 'Вторник', '09:40', 'чет', '334', '8зд'),
            ('История России', 'Вторник', '09:40', 'неч', '334', '8зд'),
            ('Высшая математика', 'Вторник', '11:20', 'общ', '334', '8зд'),
            ('Физическая культура и спорт (элективная)', 'Среда', '08:00', 'общ', 'КСК КАИ ОЛИМП', 'КСК КАИ ОЛИМПзд'),
            ('Иностранный язык', 'Среда', '09:40', 'общ', '207', '8зд'),
            ('Иностранный язык', 'Среда', '11:20', 'чет', '207', '8зд'),
            ('Высшая математика', 'Четверг', '08:00', 'общ', '516', '3зд'),
            ('Высшая математика', 'Четверг', '09:40', 'общ', '516', '3зд'),
            ('Инженерная графика', 'Четверг', '11:20', 'общ', '406', '3зд'),
            ('Физика', 'Пятница', '08:00', 'неч', '303', '2зд'),
            ('Личностное развитие', 'Пятница', '09:40', 'неч', '401', '2зд'),
            ('История России', 'Пятница', '09:40', 'чет', '401', '2зд'),
            ('Основы российской государственности', 'Пятница', '11:20', 'общ', '401', '2зд'),
            ('Высшая математика (спецкурс)', 'Пятница', '13:30', 'общ', 'Лекционный зал №1', '2зд'),
            ('Физическая культура и спорт (элективная)', 'Суббота', '08:00', 'чет', 'КСК КАИ ОЛИМП', 'КСК КАИ ОЛИМПзд'),
            ('Информатика', 'Суббота', '08:00', 'неч', '503', '3зд'),
            ('Информатика', 'Суббота', '09:40', 'неч', '503', '3зд'),
            ('Инженерная графика', 'Суббота', '11:20', 'неч', '410', '3зд'),
            ('Физическая культура и спорт', 'Суббота', '11:20', 'чет', 'ДОТ', ''),
            ('Личностное развитие', 'Суббота', '13:30', 'чет', 'ДОТ', ''),
            ('Инженерная графика', 'Суббота', '13:30', 'неч', '410', '3зд'),
            ('Теория решения изобретательских задач', 'Суббота', '15:10', 'чет', 'ДОТ', '')
        ]
        await db.executemany("INSERT INTO schedule (subject, day, time, type_week, room, building) VALUES (?, ?, ?, ?, ?, ?)", schedule_data)
        await db.commit()

def is_admin(user_id):
    return user_id in ADMIN_ID

@dp.message(Command("week_schedule"))
async def week_schedule(message: types.Message):
    async with aiosqlite.connect("university.db") as db:
        async with db.execute("SELECT subject, day, time, type_week, room, building FROM schedule") as cursor:
            rows = await cursor.fetchall()
            schedule_text = ""
            for row in rows:
                subject, day, time, type_week, room, building = row
                schedule_text += f"{day}: {time} - {subject} в {room} ({building}), {type_week} неделя\n"
            await message.answer(schedule_text)

@dp.message(Command("add_homework"))
async def add_homework(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("Эта команда только для старосты и администратора.")
        return

    data = message.text.split(",", 2)
    if len(data) != 3:
        await message.answer("Используйте формат: /add_homework Предмет, Задание, Дата сдачи")
        return
    
    subject, task, due_date = map(str.strip, data)
    subject=subject[14:]

    async with aiosqlite.connect("university.db") as db:
        await db.execute("INSERT INTO homework (subject, task, due_date) VALUES (?, ?, ?)", 
                         (subject, task, due_date))
        await db.commit()
    
    await message.answer(f"Домашка для {subject} добавлена.")

@dp.message(Command("del_homework"))
async def del_homework(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("Эта команда только для старосты и администратора.")
        return
    
    try:
        homework_id = int(message.text.split()[1])  
    except (IndexError, ValueError):
        await message.answer("Используйте формат: /del_homework ID")
        return
    
    async with aiosqlite.connect("university.db") as db:
        await db.execute("DELETE FROM homework WHERE id = ?", (homework_id,))
        await db.commit()
    
    await message.answer(f"Домашка с ID {homework_id} удалена.")

@dp.message(Command("add_event"))
async def add_event(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("Эта команда только для старосты и администратора.")
        return
    
    data = message.text.split(",", 2)
    if len(data) != 3:
        await message.answer("Используйте формат: /add_event Название, Дата, Место")
        return
    
    event_name, event_date, location = map(str.strip, data)
    event_name=event_name[11:]
    
    async with aiosqlite.connect("university.db") as db:
        await db.execute("INSERT INTO events (event_name, event_date, location) VALUES (?, ?, ?)", 
                         (event_name, event_date, location))
        await db.commit()
    
    await message.answer(f"Мероприятие '{event_name}' добавлено.")

@dp.message(Command("del_event"))
async def del_event(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("Эта команда только для старосты и администратора.")
        return
    
    try:
        event_id = int(message.text.split()[1])  
    except (IndexError, ValueError):
        await message.answer("Используйте формат: /del_event ID")
        return
    
    async with aiosqlite.connect("university.db") as db:
        await db.execute("DELETE FROM events WHERE id = ?", (event_id,))
        await db.commit()
    
    await message.answer(f"Мероприятие с ID {event_id} удалено.")

@dp.message(Command("add_material"))
async def add_material(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("Эта команда только для старосты и администратора.")
        return

    data = message.text.split(",", 1)
    if len(data) != 2:
        await message.answer("Используйте формат: /add_material Предмет, Материал")
        return
    
    subject, material = map(str.strip, data)
    subject=subject[14:]
    
    async with aiosqlite.connect("university.db") as db:
        await db.execute("INSERT INTO materials (subject, material) VALUES (?, ?)", 
                         (subject, material))
        await db.commit()
    
    await message.answer(f"Материал для {subject} добавлен.")

@dp.message(Command("del_material"))
async def del_material(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("Эта команда только для старосты и администратора.")
        return
    
    try:
        material_id = int(message.text.split()[1])  
    except (IndexError, ValueError):
        await message.answer("Используйте формат: /del_material ID")
        return
    
    async with aiosqlite.connect("university.db") as db:
        await db.execute("DELETE FROM materials WHERE id = ?", (material_id,))
        await db.commit()
    
    await message.answer(f"Материал с ID {material_id} удален.")

@dp.message(Command("materials"))
async def show_materials(message: types.Message):
    async with aiosqlite.connect("university.db") as db:
        async with db.execute("SELECT id, subject, material FROM materials") as cursor:
            materials = await cursor.fetchall()

    if materials:
        response = "Учебные материалы:\n"
        for hw_id, subject, material in materials:
            response += f"ID {hw_id} ➤ {subject}: {material}\n\n"
        await message.answer(response)
    else:
        await message.answer("Учебных материалов не найдено.")

@dp.message(Command("events"))
async def show_events(message: types.Message):
    async with aiosqlite.connect("university.db") as db:
        async with db.execute("SELECT id, event_name, event_date, location FROM events") as cursor:
            events = await cursor.fetchall()

    if events:
        response = "Предстоящие мероприятия:\n"
        for hw_id, event_name, event_date, location in events:
            response += f"ID {hw_id} ➤ {event_name}: {event_date}, {location}\n\n"
        await message.answer(response)
    else:
        await message.answer("Предстоящих мероприятий не найдено.")


@dp.message(Command("homework"))
async def show_homework(message: types.Message):
    async with aiosqlite.connect("university.db") as db:
        async with db.execute("SELECT id, subject, task, due_date FROM homework") as cursor:
            homework = await cursor.fetchall()

    if homework:
        response = "Актуальные домашние задания:\n"
        for hw_id, subject, task, due_date in homework:
            response += f"ID {hw_id} ➤ {subject}: {task} (до {due_date})\n\n"
        await message.answer(response)
    else:
        await message.answer("Актуальных домашних заданий не найдено.")

@dp.message(Command("schedule_tomorrow"))
async def show_schedule_tomorrow(message: types.Message):
    tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1)).weekday()
    day_name = get_day_name(tomorrow)

    async with aiosqlite.connect("university.db") as db:
        schedule = await get_schedule_by_day(day_name, db)

    if schedule:
        response = f"═──────{day_name}────═\n"
        for subject, time, room, building in schedule:
            response += f"➤ ⌛{time} {subject} {room} {building}\n"
        await message.answer(response)
    else:
        await message.answer(f"На {day_name} занятий не найдено.")

@dp.message(Command("schedule_today"))
async def show_schedule_today(message: types.Message):
    today = datetime.datetime.now().weekday()
    day_name = get_day_name(today)

    async with aiosqlite.connect("university.db") as db:
        schedule = await get_schedule_by_day(day_name, db)

    if schedule:
        response = f"═──────{day_name}────═\n"
        for subject, time, room, building in schedule:
            response += f"➤ ⌛{time} {subject} {room} {building}\n"
        await message.answer(response)
    else:
        await message.answer(f"На {day_name} занятий не найдено.")

@dp.message(Command("schedule_week"))
async def show_schedule_week(message: types.Message):
    async with aiosqlite.connect("university.db") as db:
        days = {}
        for i in range(6):  
            day_name = get_day_name(i)
            days[day_name] = await get_schedule_by_day(day_name, db)

    response = ""
    for day, subjects in days.items():
        if subjects:
            response += f"═──────{day}────═\n"
            for subject, time, room, building in subjects:
                response += f"➤ ⌛{time} {subject} {room} {building}\n"
            response += "\n"

    if response:
        await message.answer(f"Расписание на {current_week_type} неделю:\n{response}")
    else:
        await message.answer("Расписание не найдено.")

@dp.message(Command("admin_help"))
async def admin_help(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("Эта команда только для старосты и администратора.")
        return
    else:
        await message.answer("Доступные команды для администратора:\n"
                             "/add_homework - добавить домашнее задание\n"
                             "/del_homework - удалить домашнее задание\n"
                             "/add_event - удалить домашнее задание\n"
                             "/del_event - удалить домашнее задание\n"
                             "/add_material - удалить домашнее задание\n"
                             "/del_material - удалить домашнее задание\n")
    

@dp.message(Command("set_week"))
async def set_week(message: types.Message):
    global current_week_type  
    if current_week_type == "неч":
        current_week_type = "чет"
    else:
        current_week_type = "неч"
    await message.answer(f"Сейчас {current_week_type} неделя")

@dp.message(Command("week_check"))
async def admin_help(message: types.Message):
    await message.answer(f"Сейчас {current_week_type} неделя")

@dp.message(Command("schedule_next_week"))
async def show_schedule_next_week(message: types.Message):
    next_week_type = "неч" if current_week_type == "чет" else "чет"  

    async with aiosqlite.connect("university.db") as db:
        days = {}
        for i in range(6):  
            day_name = get_day_name(i)
            async with db.execute("SELECT DISTINCT subject, time, room, building FROM schedule WHERE day = ? AND type_week IN (?, 'общ')", (day_name, next_week_type)) as cursor:
                days[day_name] = await cursor.fetchall()

    response = f"Расписание на {next_week_type} неделю:\n"
    for day, subjects in days.items():
        if subjects:
            response += f"═──────{day}────═\n"
            for subject, time, room, building in subjects:
                response += f"➤ ⌛{time} {subject} {room} {building}\n"
            response += "\n"

    if response.strip():
        await message.answer(response)
    else:
        await message.answer(f"Расписание на {next_week_type} неделю не найдено.")

async def on_startup():
    await init_db()

if __name__ == "__main__":
    dp.startup.register(on_startup)
    dp.run_polling(bot)