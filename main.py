import flet as ft
from decimal import Decimal, InvalidOperation
import time
import asyncio
import urllib.request
import json
import math
import os
import sys
import threading
import subprocess
from games.tetris import TetrisGame

# --- КОНСТАНТЫ И НАСТРОЙКИ ---
CURRENT_VERSION = "v3.0.0"
GITHUB_REPO = "JoeMoe3910/Calculator"

# Цветовая палитра и стили
COLORS = {
    "bg_main": "#0B0E14",
    "bg_dialog": "#1E1E2E",
    "accent_purple": "#8B5CF6",
    "accent_amber": "#F59E0B",
    "accent_green": "#10B981",
    "accent_blue": "#3B82F6",
    "accent_red": "#F87171",
    "text_white": ft.Colors.WHITE,
    "text_dim": ft.Colors.WHITE54,
    "neon_purple": "#9333EA"
}

INITIAL_STATE = {
    "operand1": "0",
    "operand2": "",
    "operator": "",
    "new_operand": False,
    "history": [],
    "eq_clicks": 0,
    "c_clicks": 0,
    "key_buffer": "",
    "is_animating": False,
    "is_engineering": False,
    "abort_animation": False,
    "ans": "0",
    "display_text": "SYSTEM READY_ [v3.0.0]",
    "raw_expression": "",
    "ops_count": 0,
    "user_level": 1
}

def resource_path(relative_path):
    """Возвращает абсолютный путь к ресурсу (для PyInstaller)"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def run_stress_test():
    """Скрытая функция тестирования: 20 сложных математических операций подряд."""
    print("--- Запуск стресс-теста ---")
    operations = [
        ("1.2", "+", "2.3"), ("0.1", "+", "0.2"),
        ("100", "/", "3"), ("5", "*", "0.0001"),
        ("9999", "-", "10000"), ("1", "/", "0"),
        ("0.3", "-", "0.1"), ("10", "*", "10"),
        ("50", "+", "50"), ("123", "/", "2"),
        ("4", "*", "4"), ("8", "/", "4"),
        ("7", "+", "3"), ("9", "-", "1"),
        ("2", "*", "8"), ("10", "/", "5"),
        ("6", "+", "4"), ("3", "-", "2"),
        ("5", "*", "2"), ("100", "/", "10"),
        # Новые научные тесты
        ("math.sin(math.radians(90))",),
        ("math.sqrt(144)",),
        ("math.log10(1000)",),
        ("pow(2, 10)",)
    ]
    success_count = 0
    for i, op_tuple in enumerate(operations):
        try:
            if len(op_tuple) == 3:
                a, op, b = op_tuple
                da, db = Decimal(a), Decimal(b)
                if op == '+': res = da + db
                elif op == '-': res = da - db
                elif op == '*': res = da * db
                elif op == '/': 
                    if db == Decimal(0): res = "Деление на ноль невозможно"
                    else: res = da / db
            else:
                res = eval(op_tuple[0])
            print(f"[{i+1}/{len(operations)}] Успех: {op_tuple} = {res}")
            success_count += 1
        except Exception as e:
            print(f"[{i+1}/{len(operations)}] Ошибка: {e}")
    print(f"--- Тест завершен: {success_count}/{len(operations)} операций успешно ---")


def main(page: ft.Page):
    page.title = "Калькулятор нового поколения"
    page.bgcolor = COLORS["bg_main"]
    page.window.width = 420
    page.window.height = 850 # Возвращено по просьбе пользователя
    page.window.min_width = 400
    page.window.min_height = 800
    page.window.resizable = True
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.update()

    def show_status_dialog(title, content, release_url=None):
        def close_dialog(e):
            status_dialog.open = False
            page.update()

        def go_to_release(e):
            if release_url:
                page.launch_url(release_url)
            status_dialog.open = False
            page.update()

        actions = []
        if release_url:
            actions = [
                ft.TextButton("Да, скачать", on_click=go_to_release),
                ft.TextButton("Нет, позже", on_click=close_dialog),
            ]
        else:
            actions = [ft.TextButton("Понятно", on_click=close_dialog)]

        status_dialog = ft.AlertDialog(
            title=ft.Text(title),
            content=ft.Text(content, color=ft.Colors.WHITE70),
            actions=actions,
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor="#1E1E2E"
        )
        page.overlay.append(status_dialog)
        status_dialog.open = True
        page.update()

    def check_for_updates(e=None):
        """Ручная проверка обновлений через GitHub API"""
        page.snack_bar = ft.SnackBar(
            content=ft.Text("Поиск обновлений...", color=COLORS["text_white"]),
            bgcolor=ft.Colors.BLUE_900,
            duration=1500
        )
        page.snack_bar.open = True
        page.update()
        
        def run_manual_update_check():
            try:
                url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
                response = urllib.request.urlopen(req, timeout=5)
                data = json.loads(response.read())
                latest_version = data.get("tag_name")
                release_url = data.get("html_url")
                
                if latest_version:
                    if latest_version == CURRENT_VERSION:
                        title = "Обновлений нет"
                        msg = f"У вас установлена актуальная версия: {CURRENT_VERSION}"
                        show_status_dialog(title, msg)
                    elif latest_version < CURRENT_VERSION:
                        title = "Ого!"
                        msg = "Вы из будущего! Ваша версия выше, чем официальный релиз на GitHub."
                        show_status_dialog(title, msg)
                    else:
                        title = "Доступно обновление!"
                        msg = f"Вышла новая версия калькулятора: {latest_version}\nУ вас установлена: {CURRENT_VERSION}\n\nХотите скачать обновление сейчас?"
                        show_status_dialog(title, msg, release_url)

            except Exception:
                # Проверка на отсутствие интернета
                error_msg = "Нет подключения к интернету или сервер GitHub недоступен."
                show_status_dialog("Ошибка подключения", error_msg)

        threading.Thread(target=run_manual_update_check, daemon=True).start()


    # Состояние приложения
    calc_state = INITIAL_STATE.copy()
    calc_state["history"] = [] # Избегаем общих ссылок


    admin_dialog = ft.AlertDialog(
        title=ft.Text("МОИ СЕКРЕТИКИ 🕵️‍♂️ (v3.0.0)"),
        content=ft.Column([
            ft.Text("--- КОМАНДЫ ---", size=12, weight=ft.FontWeight.BOLD, color="#8B5CF6"),
            ft.Text("• 'admin' / 'секрет'", size=13),
            ft.Text("• 'пурпурики'", size=13),
            ft.Text("• 'hello', 'привет', 'siri'", size=13),
            ft.Text("• 'satan'", size=13),
            ft.Text("• 'potter'", size=13),
            
            ft.Text("--- ТРИГГЕРЫ ---", size=12, weight=ft.FontWeight.BOLD, color="#10B981"),
            ft.Text("• C4", size=13),
            ft.Text("• '=' до 16 раз", size=13),
            ft.Text("• Любая буква", size=13),
            
            ft.Text("--- МАТЕМАТИКА ---", size=12, weight=ft.FontWeight.BOLD, color="#F59E0B"),
            ft.Text("• 1000 - 7", size=13),
            ft.Text("• 1+1, 2+2", size=13),
            ft.Text("• 3+3+3+3", size=13),
            ft.Text("• 0.1 + 0.2", size=13),
            ft.Text("• x/0", size=13),
            ft.Text("• 10**1000", size=13),
            ft.Text("• 100000^3", size=13),
            
            ft.Text("--- РЕЗУЛЬТАТЫ ---", size=12, weight=ft.FontWeight.BOLD, color="#3B82F6"),
            ft.Text("• 1337, 777", size=13),
            ft.Text("• 666, 999", size=13),
            ft.Text("• 42, 1984", size=13),
            ft.Text("• 300, 228", size=13),
            ft.Text("• 322, 80085", size=13),
            ft.Text("• 0.07, 88", size=13),
            ft.Text("• 5051, 2048, 9000", size=13),
            ft.Text("• 11, 9.75, 67", size=13),
            ft.Text("• 69, 420, 0.3", size=13),
            ft.Text("• 0, 1, 20, 404", size=13),
            ft.Text("• 3.14, 10^1000, -x, 10^15", size=13),

        ], scroll=ft.ScrollMode.AUTO, height=450, spacing=8),
        bgcolor="#1E1E2E",
        title_padding=20,
        content_padding=20,
        actions=[
            ft.TextButton("Закопать обратно", on_click=lambda e: close_admin(e))
        ]
    )
    def close_admin(e):
        admin_dialog.open = False
        page.update()
    
    page.overlay.append(admin_dialog)

    # --- ОБОРУДОВАНИЕ И СОСТОЯНИЕ ---
    op_btns = {}
    zen_active = False
    
    # UI Элементы

    current_input = ft.Text(
        value="0", 
        size=56, 
        color=ft.Colors.WHITE, 
        weight=ft.FontWeight.W_300, 
        text_align=ft.TextAlign.RIGHT,
        animate_size=200
    )
    
    history_texts = [
        ft.Text(value="", color=ft.Colors.WHITE54, size=16, text_align=ft.TextAlign.RIGHT) 
        for _ in range(3)
    ]
    
    sarcasm_text = ft.Text(value="", color=ft.Colors.PURPLE_300, size=14, text_align=ft.TextAlign.RIGHT, max_lines=2)
    ans_label = ft.Text(value="Ans: 0", color=ft.Colors.WHITE24, size=12, text_align=ft.TextAlign.RIGHT)

    # Black Hole Background (punishment)
    black_hole_bg = ft.Image(
        src=resource_path("black_hole.png"),
        fit=ft.BoxFit.COVER,
        visible=False,
        opacity=0,
        top=0,
        left=0,
        right=0,
        bottom=0
    )
    def update_history_ui():
        """Обновляет текстовые поля истории на экране"""
        for i in range(3):
            if i < len(calc_state["history"]):
                history_texts[2-i].value = calc_state["history"][-(i+1)]
            else:
                history_texts[2-i].value = ""
        page.update()

    def add_history(entry):
        """Добавляет запись в историю вычислений"""
        if not calc_state["history"] or calc_state["history"][-1] != entry:
            calc_state["history"].append(entry)
            if len(calc_state["history"]) > 3:
                calc_state["history"].pop(0)
            update_history_ui()

    def clear_active_effects():
        """Сбрасывает все активные визуальные эффекты и пасхалки"""
        page.bgcolor = COLORS["bg_main"]
        page.title = "Калькулятор нового поколения"
        current_input.color = COLORS["text_white"]
        current_input.size = 56
        current_input.opacity = 1.0
        black_hole_bg.visible = False
        black_hole_bg.opacity = 0
        sarcasm_text.value = ""
        sarcasm_text.color = ft.Colors.PURPLE_300  # Сброс цвета после Matrix
        # Возвращаем видимость и наклон кнопки равно
        try:
             equal_btn.visible = True
             equal_btn.content.opacity = 1.0
             equal_btn.content.scale = 1.0
             equal_btn.content.rotate = 0.0
             equal_btn.content.update()
        except: pass
        page.update()



    # --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ЛОГИКИ ---

    async def run_c4_explosion():
        """Пасхалка: взрыв при 4-х нажатиях на C"""
        if zen_active: return # Дзен блокирует игры
        clear_active_effects()
        calc_state["is_animating"] = True
        
        # Обратный отсчет v3.0.0
        current_input.size = 48
        for i in [3, 2, 1]:
            current_input.value = f"C-4: {i}..."
            page.update()
            await asyncio.sleep(0.6)
            
        current_input.value = "💥 BOOM! 💥"
        page.update()
        await asyncio.sleep(0.3)

        for i in range(10):
            page.bgcolor = COLORS["accent_red"] if i % 2 == 0 else ft.Colors.BLACK
            current_input.value = ("🔥" * (i + 1))
            page.update()
            await asyncio.sleep(0.1)
        
        page.bgcolor = COLORS["bg_main"]
        current_input.size = 56
        calc_state["is_animating"] = False
        page.update()
        await asyncio.sleep(0.8)
        current_input.value = "0"
        page.update()

    async def run_ghoul_animation():
        """Пасхалка: 1000 - 7 (Гуль)"""
        calc_state["is_animating"] = True
        calc_state["abort_animation"] = False
        v = 1000
        current_input.color = ft.Colors.RED
        current_input.size = 40
        while v > 0:
            if calc_state.get("abort_animation", False):
                break
            old_v = v
            v -= 7
            current_input.value = f"{v} - 7 ="
            add_history(f"{old_v} - 7 = {v}")
            page.update()
            await asyncio.sleep(0.02) # Ускорено для v3.0.0
        
        if calc_state.get("abort_animation", False):
            current_input.color = COLORS["text_white"]
            current_input.value = "0"
            current_input.size = 56
            sarcasm_text.value = "Отсчёт прерван."
            calc_state["raw_expression"] = ""
            calc_state["new_operand"] = False
            calc_state["is_animating"] = False
            calc_state["abort_animation"] = False
        else:
            current_input.value = "Я ГУЛЬ 🩸"
            current_input.size = 56
            page.update()
            await asyncio.sleep(1.5)
            current_input.color = COLORS["text_white"]
            current_input.value = "993"
            sarcasm_text.value = "Я гуль... 1000 - 7 = 993... 🖤"
            calc_state["raw_expression"] = "993"
            calc_state["ans"] = "993"
            calc_state["new_operand"] = True
            calc_state["is_animating"] = False
        page.update()

    async def run_jackpot_effect():
        """Эффект: Джекпот при 777"""
        clear_active_effects()
        sarcasm_text.value = "JACKPOT! Беги покупать лотерейный билет! 💰"
        calc_state["is_animating"] = True
        for _ in range(10):
             page.bgcolor = ft.Colors.AMBER_400 if page.bgcolor != ft.Colors.AMBER_400 else ft.Colors.BLACK
             page.update()
             await asyncio.sleep(0.08)
        page.bgcolor = COLORS["bg_main"]
        calc_state["is_animating"] = False
        page.update()

    async def run_matrix_mode():
        """Эффект: Режим Матрицы при 1337 (v3.0.0 Edition)"""
        clear_active_effects()
        calc_state["is_animating"] = True
        calc_state["display_text"] = "!!! OVERRIDE_INITIATED !!!"
        update_monitor()
        
        # Начальный глитч
        for i in range(25): # Удлинено для v3.0.0
            page.bgcolor = "#001A00" if i % 2 == 0 else "#000000"
            current_input.value = "".join([chr(bytearray(os.urandom(1))[0] % 26 + 65) for _ in range(8)])
            current_input.color = "#00FF41"
            monitor_content.value = f"ANALYZING_CORE_{i}...\nDATA_BREACH: {i*4}%"
            page.update()
            await asyncio.sleep(0.04)
        
        page.bgcolor = "#050505"
        page.title = "ACCESS_GRANTED_CORE"
        current_input.value = "NEO"
        current_input.size = 72
        current_input.color = "#00FF41"
        
        sarcasm_text.value = "Проснись, Нео... Ты погряз в вычислениях. 🐇"
        sarcasm_text.color = "#00FF41"
        
        calc_state["is_animating"] = False
        calc_state["display_text"] = "LOCAL_RECONFIGURATION..."
        update_monitor()
        page.update()

    async def run_glitch_division():
        """Ошибка сингулярности (v3.0.0 Edition)"""
        clear_active_effects()
        calc_state["is_animating"] = True
        calc_state["display_text"] = "SINGULARITY_DETECTED!"
        update_monitor()
        
        for i in range(20):
            page.bgcolor = ft.Colors.RED_900 if i % 2 == 0 else ft.Colors.INDIGO_900
            current_input.value = "ERR_VOID" if i % 3 == 0 else "NULL"
            current_input.size = 20 + (i * 2)
            page.update()
            await asyncio.sleep(0.04)
        
        # Активация черной дыры
        page.bgcolor = "#000000"
        black_hole_bg.visible = True
        black_hole_bg.opacity = 1
        current_input.value = "V O I D"
        current_input.size = 84 # Огромный текст
        current_input.opacity = 1.0 # Полная видимость
        current_input.color = ft.Colors.RED_ACCENT_400 # Кислотно-красный
        
        sarcasm_text.value = "СИНГУЛЯРНОСТЬ ДОСТИГНУТА"
        sarcasm_text.color = ft.Colors.WHITE
        sarcasm_text.weight = ft.FontWeight.BOLD
        
        calc_state.update({"raw_expression": "0", "ans": "0", "new_operand": True, "is_animating": False, "display_text": "THE_END_OF_ALL"})
        update_monitor()
        page.update()
        
        await asyncio.sleep(15) # Сокращено до 15 сек в v3.0.0
        if black_hole_bg.visible:
            clear_active_effects()
            calc_state["display_text"] = "SYSTEM_RESTORED"
            update_monitor()
            page.update()

    def calculate_scientific(data, target_operand):
        """Логика научных расчетов"""
        try:
            val = float(calc_state[target_operand])
            if data == "sin": res = math.sin(math.radians(val))
            elif data == "cos": res = math.cos(math.radians(val))
            elif data == "tan": res = math.tan(math.radians(val))
            elif data == "sqrt": 
                if val < 0: raise ValueError
                res = math.sqrt(val)
            elif data == "log": res = math.log10(val)
            elif data == "ln": res = math.log(val)
            elif data == "abs": res = abs(val)
            elif data == "fact": res = math.factorial(int(val))
            elif data == "sq2": res = val ** 2
            elif data == "sq3": res = val ** 3
            else: res = val
            
            res_str = f"{res:g}"
            calc_state[target_operand] = res_str
            current_input.value = format_number_scale(res_str)
            sarcasm_text.value = "Научные расчеты — залог точности!"
        except Exception:
            current_input.value = "Ошибка"
        page.update()


    def format_number_scale(text_val):
        # Умное масштабирование шрифта
        length = len(text_val)
        if length > 12:
            current_input.size = 32
        elif length > 8:
            current_input.size = 44
        else:
            current_input.size = 56
        return text_val

    def evaluate_safely(expression):
        """Безопасная оценка математического выражения"""
        safe_names = {
            'sin': lambda x: math.sin(math.radians(x)),
            'cos': lambda x: math.cos(math.radians(x)),
            'tan': lambda x: math.tan(math.radians(x)),
            'sqrt': math.sqrt,
            'log': math.log10,
            'ln': math.log,
            'abs': abs,
            'fact': math.factorial,
            'pi': math.pi,
            'e': math.e,
        }
        # Заменяем визуальные символы на программные
        expr = expression.replace("×", "*").replace("÷", "/").replace("^", "**")
        try:
            res = eval(expr, {"__builtins__": None}, safe_names)
            return res
        except ZeroDivisionError:
            return "SINGULARITY"
        except: return None

    def process_input(data):
        if calc_state.get("is_animating", False):
            if data in ["AC", "C", "BACKSPACE"]: calc_state["abort_animation"] = True
            return
        if not data: return
        
        # Пасхалка: буквы
        if data.startswith("LETTER_"):
            sarcasm_text.value = "Я калькулятор, а не текстовый редактор! Перестань жать на кнопки! ⌨️"
            page.update()
            return

        # Пасхалка: нажатие 'C' 4 раза (C4)
        if data == "C":
            if not zen_active:
                calc_state["c_clicks"] += 1
                if calc_state["c_clicks"] == 4:
                    page.run_task(run_c4_explosion)
                    calc_state["c_clicks"] = 0
                    return
            else: calc_state["c_clicks"] = 0
        elif data != "BACKSPACE": 
            calc_state["c_clicks"] = 0

        # Очистка
        if data == "AC":
            calc_state.update(INITIAL_STATE.copy())
            calc_state["history"] = []
            current_input.value = "0"
            sarcasm_text.value = ""
            update_history_ui()
            clear_active_effects()
            page.update()
            return

        # Очистка текущего ввода
        if data == "C":
            calc_state["raw_expression"] = ""
            calc_state["new_operand"] = False
            current_input.value = "0"
            sarcasm_text.value = ""
            page.update()
            return

        # Удаление последнего символа
        if data == "BACKSPACE":
            if calc_state["raw_expression"]:
                e = calc_state["raw_expression"].strip()
                if e.endswith(("+", "-", "*", "/", "^")):
                    calc_state["raw_expression"] = e[:-1].strip()
                else:
                    calc_state["raw_expression"] = e[:-1]
            current_input.value = calc_state["raw_expression"] or "0"
            page.update()
            return

        # Числа
        if data in ["0","1","2","3","4","5","6","7","8","9","."]:
            if calc_state["new_operand"]:
                calc_state["raw_expression"] = data if data != "." else "0."
                calc_state["new_operand"] = False
            else:
                if calc_state["raw_expression"] == "0" and data != ".":
                    calc_state["raw_expression"] = data
                else:
                    calc_state["raw_expression"] += data
            current_input.value = calc_state["raw_expression"]
            page.update()
            return

        # Операторы
        if data in ["+", "-", "*", "/", "^"]:
            if calc_state["new_operand"]: calc_state["new_operand"] = False
            if not calc_state["raw_expression"]: calc_state["raw_expression"] = calc_state["ans"]
            
            # Замена оператора
            expr = calc_state["raw_expression"].rstrip()
            if expr.endswith(("+", "-", "*", "/", "^")):
                calc_state["raw_expression"] = expr[:-1].strip()
            
            calc_state["raw_expression"] += f" {data} "
            current_input.value = calc_state["raw_expression"]
            page.update()
            return

        # Специальное научное
        if data in ["sin", "cos", "tan", "sqrt", "log", "ln", "abs", "fact", "sq2", "sq3"]:
            if data == "sq2": calc_state["raw_expression"] = f"({calc_state['raw_expression']})^2"
            elif data == "sq3": calc_state["raw_expression"] = f"({calc_state['raw_expression']})^3"
            else: calc_state["raw_expression"] += f"{data}("
            current_input.value = calc_state["raw_expression"]
            page.update()
            return

        if data in ["pi", "e", "Ans"]:
            val = "pi" if data=="pi" else ("e" if data=="e" else calc_state["ans"])
            calc_state["raw_expression"] += val
            current_input.value = calc_state["raw_expression"]
            page.update()
            return
            
        if data in ["(", ")"]:
            calc_state["raw_expression"] += data
            current_input.value = calc_state["raw_expression"]
            page.update()
            return

        # Результат
        if data == "=":
            # Сбрасываем эффекты перед новым вычислением (Mutex)
            if calc_state["eq_clicks"] == 0: clear_active_effects()

            # Проверка ключевых слов из буфера при нажатии на "="
            kb = calc_state["key_buffer"]
            if "hello" in kb or "привет" in kb:
                 calc_state["key_buffer"] = ""
                 sarcasm_text.value = "Привет! Я калькулятор, а не Siri 🤖"
                 page.update()
                 return
            
            calc_state["eq_clicks"] += 1
            # Прогрессия кнопки равно (используем текущее значение дисплея)
            cur_val = current_input.value
            if calc_state["eq_clicks"] == 4:
                sarcasm_text.value = f"{cur_val}={cur_val}, удовольствие получено? 😏"
            elif calc_state["eq_clicks"] == 8:
                sarcasm_text.value = "Ты пытаешься сломать кнопку равно? 🔨"
            elif calc_state["eq_clicks"] == 12:
                sarcasm_text.value = "Кнопка начинает скрипеть... 🔊"
                try: 
                    equal_btn.content.scale = 1.2
                    equal_btn.content.update()
                except: pass
            elif calc_state["eq_clicks"] == 15:
                sarcasm_text.value = "ПОСЛЕДНЕЕ ПРЕДУПРЕЖДЕНИЕ! ⚠️"
                try: 
                    equal_btn.content.scale = 1.5
                    equal_btn.content.rotate = 0.1
                    equal_btn.content.update()
                except: pass
            elif calc_state["eq_clicks"] >= 16:
                sarcasm_text.value = "Кнопка сломалась! 👋 (Для перезагрузки нажми AC)"
                try:
                    equal_btn.visible = False
                    equal_btn.update()
                except: pass
                page.update()
                return

            expr = calc_state["raw_expression"].strip()
            if not expr: return
            
            # Пасхалки входные
            clean_expr = expr.replace(" ", "")
            if clean_expr == "1000-7":
                page.run_task(run_ghoul_animation)
                return
            if clean_expr == "3+3+3+3":
                sarcasm_text.value = "Дырка! 🍩"
                page.update()
            if clean_expr == "2+2":
                sarcasm_text.value = "ПО МНЕНИЮ МИНИСТЕРСТВА ПРАВДЫ: 2+2=5 👁️"
                page.update()
            if clean_expr == "1+1":
                sarcasm_text.value = "Я тебе точно нужен? 🤨"
                page.update()
            if clean_expr == "hello" or clean_expr == "привет":
                sarcasm_text.value = "Привет! Я калькулятор, а не Siri 🤖"
                page.update()
            if "100000^3" in clean_expr or "100000**3" in clean_expr:
                sarcasm_text.value = "На твоем банковском счету никогда не будет столько нулей"
                page.update()

            res = evaluate_safely(expr)
            
            if res == "SINGULARITY":
                page.run_task(run_glitch_division)
                return

            if res is not None:
                try:
                    res_dec = Decimal(str(res))
                    res_str = f"{res_dec:f}".rstrip("0").rstrip(".") if "." in f"{res_dec:f}" else f"{res_dec:f}"
                    
                    try:
                        res_val = float(res)
                        # Пасхалки по результату (только если это был расчет, а не просто ввод числа)
                        if expr.strip() != res_str:
                            if res_val == 777: page.run_task(run_jackpot_effect)
                            elif res_val == 1337: page.run_task(run_matrix_mode)
                            elif res_val == 42: sarcasm_text.value = "Ответ на главный вопрос жизни... 🌌"
                            elif res_val == 1984: sarcasm_text.value = "БОЛЬШОЙ БРАТ СЛЕДИТ ЗА ТВОИМИ ВЫЧИСЛЕНИЯМИ 📽️"
                            elif res_val == 300: sarcasm_text.value = "Тракторист?"
                            elif res_val == 228: sarcasm_text.value = "Статья за хранение... Калькуляторов"
                            elif res_val == 322: sarcasm_text.value = "Кто-то снова решил слить катку... GGWP"
                            elif res_val == 80085: sarcasm_text.value = "BOOBS! (•)(•)"
                            elif res_val == 0.07: sarcasm_text.value = "Меня зовут Калькулятор. Просто Калькулятор. 🍸"
                            elif res_val == 88: sarcasm_text.value = "88 миль в час! Назад в будущее! 🏎️"
                            elif res_val == 666: sarcasm_text.value = "Число зверя! 🔥"
                            elif res_val == 999: sarcasm_text.value = "Переверни калькулятор!"
                            elif res_val == 5051: sarcasm_text.value = "SOSI... Очень остроумно"
                            elif res_val == 2048: sarcasm_text.value = "О нет, я снова завис в этой игре..."
                            elif res_val == 9000: sarcasm_text.value = "It's OVER 9000+! 🛡️"
                            elif res_val == 11: sarcasm_text.value = "Вы получили самое большое число!"
                            elif res_val == 9.75: sarcasm_text.value = "⚡ Платформа девять и три четверти!"
                            elif res_val == 67: sarcasm_text.value = "Six Seven! 👐"
                            elif math.isclose(res_val, 0.3, abs_tol=1e-15):
                                if "0.1" in clean_expr and "0.2" in clean_expr:
                                    sarcasm_text.value = "Так надо, повверь"
                                else:
                                    # Расширенное обнаружение для float результата
                                    if len(str(res)) > 15:
                                        sarcasm_text.value = "Так надо, повверь"
                                    else:
                                        sarcasm_text.value = "Так надо, повверь"
                            elif res_val == 69: sarcasm_text.value = "Nice."
                            elif res_val == 420: sarcasm_text.value = "Время... Расслабиться 🌿"
                            elif res_val == 0: sarcasm_text.value = "Ничего. Как и всегда."
                            elif res_val == 1: sarcasm_text.value = "Критическая неудача! 🎲"
                            elif res_val == 20: sarcasm_text.value = "Критическая удача! 🎲✨"
                            elif res_val == 404: sarcasm_text.value = "Ошибка: ответ не найден"
                            elif res_val == 3.14: sarcasm_text.value = "π🚪"
                            elif res_val == float('inf'): sarcasm_text.value = "Ты разломал пространство-время! 🌌"
                            elif res_val < 0: sarcasm_text.value = "Отрицательно... прямо как на твоем счету."
                            elif res_val > 10**15: sarcasm_text.value = "Моя голова сейчас взорвется от таких чисел! 🤯"
                    except (OverflowError, ValueError):
                        # Для слишком больших чисел (10^1000)
                        sarcasm_text.value = "Ты разломал пространство-время! 🌌"
                        res_str = "∞"
                    
                except: res_str = "∞"
                
                add_history(f"{expr} = {res_str}")
                calc_state["ans"] = res_str
                ans_label.value = f"Ans: {res_str}"
                calc_state["raw_expression"] = res_str
                calc_state["new_operand"] = True
                current_input.value = res_str
            else:
                current_input.value = "Error"
            page.update()
            return
        else:
            # Сброс счетчика Равно при любом другом действии
            calc_state["eq_clicks"] = 0
            # Каждое новое действие сбрасывает визуальные эффекты
            if data != "C": clear_active_effects()

    def on_button_click(e):
        process_input(e.control.data)

    def on_keyboard(e):
        if custom_drawer.left == 0: return
        key = e.key
        if key.startswith("Numpad "):
            key = key.replace("Numpad ", "")
            if key == "Divide": key = "/"
            elif key == "Multiply": key = "*"
            elif key == "Subtract": key = "-"
            elif key == "Add": key = "+"
        
        # Buffer для секретов (admin и т.д.)
        calc_state["key_buffer"] += key.lower()
        # Если есть e.character, добавляем его тоже для поддержки разных раскладок
        if hasattr(e, "character") and e.character:
            calc_state["key_buffer"] += e.character.lower()
            
        calc_state["key_buffer"] = calc_state["key_buffer"][-30:] # Увеличено для длинных слов
        
        # Секреты клавиатуры
        kb = calc_state["key_buffer"]
        
        # Реактивные секреты (срабатывают сразу)
        if any(h in kb for h in ["hello", "привет", "siri", "ghbdtn"]):
             calc_state["key_buffer"] = ""
             sarcasm_text.value = "Привет! Я калькулятор, а не Siri 🤖"
             page.update()
             return

        if key in ["Enter", "Numpad Enter", "="]:
             # Здесь можно оставить другие проверки для Enter
             pass

        if "пурпурики" in kb or "gehgehbrb" in kb:
             calc_state["key_buffer"] = ""
             # Запуск тетриса в новом окне через отдельный поток
             threading.Thread(target=lambda: ft.app(target=TetrisGame), daemon=True).start()
             return
        if any(kw in kb for kw in ["admin", "фвьшт", "секрет", "ctrhtn"]):
            calc_state["key_buffer"] = ""
            admin_dialog.open = True
            page.update()
            return
        if "cccc" in kb or "сссс" in kb:
            calc_state["key_buffer"] = ""
            page.run_task(run_c4_explosion)
            return
        if any(s in kb for s in ["satan", "сатана", "vfyj"]):
            calc_state["key_buffer"] = ""
            sarcasm_text.value = "👿 ТЫ ПРИЗВАЛ КОГО-ТО НЕ ТОГО"
            page.update()
            return
        if "potter" in kb or "поттер" in kb:
            calc_state["key_buffer"] = ""
            sarcasm_text.value = "⚡ ВИНГАРДИУМ ЛЕВИОССА!"
            page.update()
            return
            
        # Пасхалка на буквы
        if len(key) == 1 and key.isalpha() and key.isascii():
            process_input("LETTER_" + key)
            return

        if key in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", ".", "+", "-", "*", "/", "(", ")", "^", "="]:
            if e.shift:
                if key == "9": process_input("(")
                elif key == "0": process_input(")")
                elif key == "6": process_input("^")
                elif key == "=": process_input("+")
                else: process_input(key)
            else:
                if key == "=": process_input("=")
                else: process_input(key)
        elif key in ["Enter", "Numpad Enter"]:
            process_input("=")
        elif key == "Escape":
            process_input("AC")
        elif key in ["Backspace"]:
            process_input("BACKSPACE")
        elif key == "Delete":
            process_input("AC") # Delete стирает всё

    # --- Фоновые процессы ---
    async def monitor_flicker():
        """Имитация мерцания старого CRT монитора"""
        while True:
            if calc_state["is_engineering"] and not calc_state["is_animating"]:
                engineering_monitor.opacity = 0.8 + (math.sin(time.time() * 10) * 0.1)
                try: 
                    engineering_monitor.update()
                except: pass
            await asyncio.sleep(0.05)

    def on_load():
        page.run_task(monitor_flicker)
    
    # Регистрация инициализации
    threading.Timer(0.1, on_load).start()

    def create_btn(text, data=None, color=COLORS["text_white"], is_neon=False, width=75, bgcolor=None, font_size=28):
        """Создает стилизованную кнопку калькулятора"""
        if data is None: data = text
        
        # Стилизация (Glassmorphism / Neon)
        final_bgcolor = bgcolor if bgcolor else (ft.Colors.TRANSPARENT if is_neon else ft.Colors.with_opacity(0.05, COLORS["text_white"]))
        shadow_color = COLORS["neon_purple"] if is_neon else ft.Colors.BLACK26
        
        content = ft.Container(
            content=ft.Text(text, size=font_size, color=color, weight=ft.FontWeight.W_400),
            alignment=ft.Alignment.CENTER,
            width=width,
            height=70,
            border_radius=20,
            bgcolor=final_bgcolor,
            blur=ft.Blur(5, 5) if not bgcolor else None,
            border=ft.Border.all(1, ft.Colors.with_opacity(0.05, COLORS["text_white"])) if not bgcolor else None,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10 if is_neon else 5,
                color=shadow_color if is_neon else ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                offset=ft.Offset(0, 2)
            ),
            animate=ft.Animation(200, "easeOut")
        )
        
        def on_hover(e):
            e.control.content.scale = 1.05 if e.data == "true" else 1.0
            e.control.content.shadow.blur_radius = 20 if e.data == "true" and is_neon else (15 if is_neon else 5)
            e.control.content.update()

        btn = ft.GestureDetector(
            content=content,
            on_tap=on_button_click,
            data=data,
            on_hover=on_hover
        )
        if data in ["/", "*", "-", "+", "=", "C", "AC"]:
             op_btns[data] = btn
        return btn



    # --- Режим "Дзен" ---
    zen_active = False
    
    history_container = None
    drawer_btn = None
    zen_btn = None
    science_btn = None

    def toggle_zen(e):
        """Переключает режим 'Дзен' для v3.0.0"""
        nonlocal zen_active
        zen_active = not zen_active
        
        # Сбрасываем визуальные эффекты при переключении
        clear_active_effects()

        if history_container: 
            history_container.opacity = 0 if zen_active else 1
            history_container.visible = not zen_active
        
        zen_btn.icon = ft.Icons.SELF_IMPROVEMENT if zen_active else ft.Icons.SELF_IMPROVEMENT_OUTLINED
        zen_btn.icon_color = COLORS["accent_purple"] if zen_active else ft.Colors.WHITE54
        
        # Обновляем монитор
        update_monitor()
        page.update()

    def update_monitor():
        """Обновляет содержимое 'экранчика' инженерного режима (v3.0.0 CRT)"""
        if not calc_state["is_engineering"]: return
        
        if zen_active:
            # В Дзене монитор показывает минималистичную 'волну' или выключен
            monitor_content.value = "ZEN_MODE: ACTIVE\n[PURE_MATHEMATICS]"
            monitor_content.color = ft.Colors.WHITE24
        else:
            # Многофункциональный дисплей (RPG Stats + Progress Bar)
            monitor_content.color = "#00FF41"
            xp_needed = 10
            xp_current = calc_state["ops_count"] % xp_needed
            progress = "■" * xp_current + "□" * (xp_needed - xp_current)
            
            stats = f"LVL: {calc_state['user_level']} [{progress}]"
            monitor_content.value = f"SYSTEM_STATUS: {calc_state['display_text']}\n{stats}\nEXPR_BUFFER: {calc_state['operator'] or 'IDLE'}"
        page.update()


    def toggle_engineering(e, force_state=None):
        if force_state is not None:
            calc_state["is_engineering"] = force_state
        else:
            calc_state["is_engineering"] = not calc_state["is_engineering"]
        
        # Отключаем авто-ресайз если окно было изменено пользователем
        # Flet ловит resize, но мы упростим: если текущая ширина сильно отличается от целевой, не трогаем
        current_w = page.window.width
        is_std = abs(current_w - 420) < 10
        is_eng = abs(current_w - 800) < 10
        should_resize = is_std or is_eng
        
        if calc_state["is_engineering"]:
            engineering_buttons_area.visible = True
            centered_content.width = 750
            if should_resize: page.window.width = 800
            science_btn.icon = ft.Icons.SCIENCE
            science_btn.icon_color = "#F59E0B"
            update_monitor()
        else:
            engineering_buttons_area.visible = False
            centered_content.width = 420
            if should_resize: page.window.width = 420
            science_btn.icon = ft.Icons.SCIENCE_OUTLINED
            science_btn.icon_color = ft.Colors.WHITE54
        page.update()

    zen_btn = ft.IconButton(
        icon=ft.Icons.SELF_IMPROVEMENT_OUTLINED, 
        icon_color=ft.Colors.WHITE54,
        on_click=toggle_zen,
        tooltip="Режим Дзен"
    )

    science_btn = ft.IconButton(
        icon=ft.Icons.SCIENCE_OUTLINED,
        icon_color=ft.Colors.WHITE54,
        on_click=toggle_engineering,
        tooltip="Инженерный калькулятор"
    )
    
    def open_drawer(e):
        custom_drawer.left = 0
        custom_drawer.update()

    drawer_btn = ft.IconButton(
        icon=ft.Icons.MENU,
        icon_color=ft.Colors.WHITE54,
        on_click=open_drawer,
        tooltip="Умный конвертер"
    )

    def toggle_converter(e):
        """Переключает режим Конвертера (полноэкранный режим v3.2.0)"""
        is_visible = not converter_panel.visible
        converter_panel.visible = is_visible
        
        # Полностью скрываем элементы калькулятора
        buttons_area.visible = not is_visible
        display_area.visible = not is_visible 
        
        if is_visible:
             update_rates_and_convert()
             # При открытии запускаем обновление валют в фоне
             threading.Thread(target=fetch_live_rates, daemon=True).start()
             if zen_active:
                 engineering_buttons_area.visible = False
                 science_btn.icon = ft.Icons.SCIENCE_OUTLINED
                 science_btn.icon_color = ft.Colors.WHITE54
             
             # Правило: в конвертере нельзя открыть инженерный режим
             science_btn.disabled = True
             science_btn.tooltip = "Отключено в режиме конвертера"
        else:
             science_btn.disabled = False
             science_btn.tooltip = "Инженерный режим"
        
        conv_btn.icon = ft.Icons.CURRENCY_EXCHANGE if not is_visible else ft.Icons.CALCULATE
        conv_btn.icon_color = COLORS["accent_green"] if is_visible else ft.Colors.WHITE54
        page.update()

    def update_rates_and_convert(e=None):
        """Продвинутая логика конвертации (v3.2.1)"""
        val_str = conv_input.value.replace(",", ".") if conv_input.value else "0"
        try:
            val = Decimal(val_str)
        except: return

        res = Decimal(0)
        f, t = conv_from_dd.value, conv_to_dd.value
        
        if conv_mode == "currency":
            res = val * Decimal(str(converter_rates.get(f, 1.0))) / Decimal(str(converter_rates.get(t, 1.0)))
        
        elif conv_mode == "weight":
            w_rates = {"KG": 1.0, "LB": 0.4536, "OZ": 0.02835, "G": 0.001}
            res = val * Decimal(str(w_rates.get(f, 1.0))) / Decimal(str(w_rates.get(t, 1.0)))

        elif conv_mode == "length":
            l_rates = {"M": 1.0, "FT": 0.3048, "IN": 0.0254, "CM": 0.01}
            res = val * Decimal(str(l_rates.get(f, 1.0))) / Decimal(str(l_rates.get(t, 1.0)))
        
        elif conv_mode == "temp":
            if f == t: res = val
            elif f == "C": res = val * 9/5 + 32 if t == "F" else val + Decimal("273.15")
            elif f == "F": res = (val - 32) * 5/9 if t == "C" else (val - 32) * 5/9 + Decimal("273.15")
            elif f == "K": res = val - Decimal("273.15") if t == "C" else (val - Decimal("273.15")) * 9/5 + 32

        elif conv_mode == "speed":
            s_rates = {"KM/H": 1.0, "M/S": 3.6, "MPH": 1.60934}
            res = val * Decimal(str(s_rates.get(f, 1.0))) / Decimal(str(s_rates.get(t, 1.0)))
            
        conv_res_text.value = f"{res:.4f}".rstrip('0').rstrip('.')
        page.update()

    conv_btn = ft.IconButton(
        icon=ft.Icons.CURRENCY_EXCHANGE_OUTLINED,
        icon_color=ft.Colors.WHITE54,
        on_click=toggle_converter,
        tooltip="Конвертер"
    )

    top_bar = ft.Container(
        content=ft.Row(
            controls=[
                drawer_btn,
                ft.Row([conv_btn, science_btn, zen_btn], spacing=0)
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=ft.Padding(left=10, right=10, top=10, bottom=0)
    )

    def change_conv_mode(e):
        nonlocal conv_mode
        conv_mode = e.control.data
        
        # Обновляем опции выпадающих списков
        options_map = {
            "currency": ["RUB", "USD", "EUR", "GEL", "KZT"],
            "weight": ["KG", "LB", "OZ", "G"],
            "length": ["M", "FT", "IN", "CM"],
            "temp": ["C", "F", "K"],
            "speed": ["KM/H", "M/S", "MPH"]
        }
        new_opts = [ft.dropdown.Option(x) for x in options_map[conv_mode]]
        conv_from_dd.options = new_opts
        conv_to_dd.options = new_opts
        conv_from_dd.value = options_map[conv_mode][0]
        conv_to_dd.value = options_map[conv_mode][1] if len(options_map[conv_mode]) > 1 else options_map[conv_mode][0]
        
        for btn in [m_curr_btn, m_weight_btn, m_length_btn, m_temp_btn, m_speed_btn]:
            btn.style = ft.ButtonStyle(bgcolor=ft.Colors.TRANSPARENT, color=ft.Colors.WHITE30)
        e.control.style = ft.ButtonStyle(bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE), color=COLORS["accent_purple"])
        
        update_rates_and_convert()
        page.update()

    # --- UI КОМПОНЕНТЫ ---

    def create_display_area():
        """Создает область экрана калькулятора"""
        nonlocal history_container
        history_container = ft.Container(
            content=ft.Column(
                controls=history_texts, 
                spacing=2, 
                alignment=ft.MainAxisAlignment.END,
                horizontal_alignment=ft.CrossAxisAlignment.END,
                scroll=ft.ScrollMode.HIDDEN
            ),
            height=90,
        )
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    history_container,
                    ft.Container(
                        content=sarcasm_text,
                        height=45,
                        alignment=ft.Alignment.TOP_RIGHT,
                    ),
                    ans_label,
                    current_input
                ],
                alignment=ft.MainAxisAlignment.END,
                horizontal_alignment=ft.CrossAxisAlignment.END,
                spacing=0
            ),
            padding=ft.Padding(25, 0, 25, 20),
            height=300, 
            alignment=ft.Alignment.BOTTOM_RIGHT
        )

    # display_area создается ниже, после create_converter_drawer

    # --- РЕЖИМ КОНВЕРТЕРА ---
    conv_mode = "currency"
    BASE_RATES_PATH = resource_path("converter_rates.json")
    
    def get_cached_rates():
        try:
            if os.path.exists(BASE_RATES_PATH):
                with open(BASE_RATES_PATH, "r") as f:
                    return json.load(f)
        except Exception: pass
        return {"USD": 95.0, "EUR": 102.0, "GEL": 35.0, "RUB": 1.0, "KZT": 0.2}

    converter_rates = get_cached_rates()

    def fetch_live_rates():
        nonlocal converter_rates
        try:
            url = "https://api.exchangerate-api.com/v4/latest/RUB"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read())
                raw_rates = data.get("rates", {})
                if raw_rates:
                    new_rates = {"RUB": 1.0}
                    for cur in ["USD", "EUR", "GEL", "KZT"]:
                        if raw_rates.get(cur):
                            new_rates[cur] = round(1 / raw_rates[cur], 4)
                    converter_rates = new_rates
                    with open(BASE_RATES_PATH, "w") as f:
                        json.dump(new_rates, f)
                    if converter_panel.visible:
                        page.run_task(update_rates_and_convert)
        except Exception: pass

    # Кнопки режимов
    mode_btn_style = lambda active: ft.ButtonStyle(
        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE) if active else ft.Colors.TRANSPARENT,
        color=COLORS["accent_purple"] if active else ft.Colors.WHITE30,
        shape=ft.CircleBorder(),
        padding=10
    )
    
    m_curr_btn = ft.IconButton(icon=ft.Icons.MONETIZATION_ON, data="currency", on_click=change_conv_mode, style=mode_btn_style(True))
    m_weight_btn = ft.IconButton(icon=ft.Icons.SCALE, data="weight", on_click=change_conv_mode, style=mode_btn_style(False))
    m_length_btn = ft.IconButton(icon=ft.Icons.STRAIGHTEN, data="length", on_click=change_conv_mode, style=mode_btn_style(False))
    m_temp_btn = ft.IconButton(icon=ft.Icons.THERMOSTAT, data="temp", on_click=change_conv_mode, style=mode_btn_style(False))
    m_speed_btn = ft.IconButton(icon=ft.Icons.SPEED, data="speed", on_click=change_conv_mode, style=mode_btn_style(False))

    def swap_converter_units(e):
        """Меняет местами единицы в конвертере"""
        f, t = conv_from_dd.value, conv_to_dd.value
        conv_from_dd.value, conv_to_dd.value = t, f
        update_rates_and_convert()
        page.update()

    # Универсальные селекторы
    conv_from_dd = ft.Dropdown(options=[ft.dropdown.Option(x) for x in ["RUB", "USD", "EUR", "GEL", "KZT"]], value="RUB", width=120, on_select=update_rates_and_convert)
    conv_to_dd = ft.Dropdown(options=[ft.dropdown.Option(x) for x in ["USD", "EUR", "GEL", "RUB", "KZT"]], value="USD", width=120, on_select=update_rates_and_convert)
    
    universal_row = ft.Row([
        conv_from_dd, 
        ft.IconButton(icon=ft.Icons.SWAP_HORIZ, icon_color=ft.Colors.WHITE24, on_click=swap_converter_units),
        conv_to_dd
    ], alignment=ft.MainAxisAlignment.CENTER)
    
    conv_res_text = ft.Text("0.00", size=32, weight=ft.FontWeight.W_300, color=ft.Colors.WHITE)

    conv_input = ft.TextField(
        label="Значение", 
        dense=True,
        color=ft.Colors.WHITE, 
        border_color=COLORS["accent_purple"],
        focused_border_color=COLORS["accent_purple"],
        width=200,
        text_align=ft.TextAlign.CENTER,
        text_size=18,
        on_change=update_rates_and_convert
    )

    converter_panel = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Container(
                    content=ft.Text("SYSTEM CONVERTER", size=14, color=COLORS["accent_purple"], weight=ft.FontWeight.BOLD),
                    padding=ft.Padding(10, 5, 10, 5),
                    border=ft.Border.all(1, ft.Colors.with_opacity(0.2, COLORS["accent_purple"])),
                    border_radius=5
                ),
                ft.IconButton(icon=ft.Icons.CLOSE, icon_color=ft.Colors.WHITE24, on_click=toggle_converter)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            
            ft.Container(height=20),
            
            # Селектор режимов (Glassmorphism row)
            ft.Container(
                content=ft.Row([m_curr_btn, m_weight_btn, m_length_btn, m_temp_btn, m_speed_btn], alignment=ft.MainAxisAlignment.CENTER),
                bgcolor=ft.Colors.with_opacity(0.03, ft.Colors.WHITE),
                padding=10,
                border_radius=15,
                border=ft.Border.all(1, ft.Colors.with_opacity(0.05, ft.Colors.WHITE))
            ),
            
            ft.Container(height=40),
            
            # Поле ввода
            ft.Container(
                content=conv_input,
                alignment=ft.Alignment(0, 0),
            ),
            
            ft.Container(height=20),
            
            # Селекторы единиц
            universal_row,
            
            ft.Container(height=40),
            
            # Результат (Glow effect card)
            ft.Container(
                content=ft.Column([
                    ft.Text("РЕЗУЛЬТАТ", size=10, color=ft.Colors.WHITE30, weight=ft.FontWeight.BOLD),
                    conv_res_text,
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                padding=25,
                width=300,
                border_radius=20,
                bgcolor=ft.Colors.BLACK,
                border=ft.Border.all(1, ft.Colors.with_opacity(0.1, COLORS["accent_purple"])),
                shadow=ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=30,
                    color=ft.Colors.with_opacity(0.15, COLORS["accent_purple"]),
                    offset=ft.Offset(0, 0)
                ),
                gradient=ft.LinearGradient(
                    begin=ft.Alignment(-1, -1),
                    end=ft.Alignment(1, 1),
                    colors=[ft.Colors.with_opacity(0.05, COLORS["accent_purple"]), ft.Colors.TRANSPARENT]
                )
            ),
        ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        padding=ft.Padding(25, 20, 25, 20),
        visible=False,
        animate_opacity=300,
        bgcolor=ft.Colors.BLACK,
        expand=True,
        height=650
    )


    def create_converter_drawer():
        """Создает боковую панель (только ссылки в v3.0.0)"""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row([
                        ft.Text("Меню", size=20, weight=ft.FontWeight.W_600, color=COLORS["accent_purple"]),
                        ft.IconButton(icon=ft.Icons.CLOSE, on_click=lambda _: close_drawer(), icon_color=COLORS["text_dim"])
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Divider(color=ft.Colors.WHITE24),
                    ft.TextButton("Telegram Канал", icon=ft.Icons.SEND, url="https://t.me/JoeMoeCode", icon_color=COLORS["accent_purple"]),
                    ft.TextButton("Сообщить о баге", icon=ft.Icons.BUG_REPORT, url=f"https://github.com/{GITHUB_REPO}/issues", icon_color=COLORS["accent_red"]),
                    ft.TextButton("Проверить обновления", icon=ft.Icons.REFRESH, on_click=check_for_updates, icon_color=COLORS["accent_blue"]),
                    ft.Divider(color=ft.Colors.WHITE24),
                    ft.Text("Калькулятор v3.0.0", color=COLORS["text_dim"], size=12)
                ]
            ),
            left=-400, top=0, bottom=0, width=320, bgcolor="#121620", padding=20,
            animate_position=400, shadow=ft.BoxShadow(spread_radius=10, blur_radius=50, color=ft.Colors.BLACK54)
        )

    def close_drawer():
        custom_drawer.left = -400
        page.update()

    display_area = create_display_area()
    custom_drawer = create_converter_drawer()


    # --- Инженерные кнопки и 'экранчик' ---
    monitor_content = ft.Text(
        "BOOTING_SYSTEM...", 
        size=13, 
        color="#00FF41", # Classic Matrix Green
        font_family="monospace",
    )
    
    engineering_monitor = ft.Container(
        content=monitor_content,
        bgcolor="#001100", # Darker green background
        padding=12,
        border_radius=5,
        border=ft.Border.all(2, "#00FF41"),
        height=90,
        margin=ft.Margin(0, 0, 0, 15),
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=15,
            color=ft.Colors.with_opacity(0.3, "#00FF41")
        ),
        animate=ft.Animation(300, "easeIn")
    )

    engineering_buttons_area = ft.Container(
        content=ft.Column(
            controls=[
                engineering_monitor,
                ft.Row([
                    create_btn("sin", font_size=16), 
                    create_btn("cos", font_size=16), 
                    create_btn("tan", font_size=16),
                    create_btn("xʸ", "^", font_size=16)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([
                    create_btn("√", "sqrt", font_size=18), 
                    create_btn("log", font_size=16), 
                    create_btn("ln", font_size=16),
                    create_btn("x²", "sq2", font_size=18)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([
                    create_btn("x³", "sq3", font_size=18), 
                    create_btn("abs", font_size=16), 
                    create_btn("n!", "fact", font_size=18),
                    create_btn("π", "pi", font_size=24) # Перемещено
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([
                    create_btn("e", font_size=24), # Перемещено
                    create_btn("(", "(", color="#10B981", font_size=20), # Перемещено
                    create_btn(")", ")", color="#10B981", font_size=20), # Перемещено
                    create_btn("mod", "%", font_size=16)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ],
            spacing=10
        ),
        padding=ft.Padding(25, 25, 0, 25),
        visible=False,
        width=350
    )

    # --- Кнопки калькулятора ---
    buttons_area = ft.Container(
        content=ft.Column(
            controls=[
                ft.Row([
                    create_btn("AC", "AC", color="#F87171"), 
                    create_btn("C", "C", color="#F87171"), 
                    create_btn("%", "%", color="#10B981"), 
                    create_btn("÷", "/", color=ft.Colors.WHITE, is_neon=True)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([
                    create_btn("7"), create_btn("8"), create_btn("9"), 
                    create_btn("×", "*", color=ft.Colors.WHITE, is_neon=True)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([
                    create_btn("4"), create_btn("5"), create_btn("6"), 
                    create_btn("-", "-", color=ft.Colors.WHITE, is_neon=True)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([
                    create_btn("1"), create_btn("2"), create_btn("3"), 
                    create_btn("+", "+", color=ft.Colors.WHITE, is_neon=True)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([
                    create_btn("0", width=165), 
                    create_btn("."), 
                    equal_btn := create_btn("=", "=", color=COLORS["text_white"], bgcolor=COLORS["accent_blue"], is_neon=True)
                ], spacing=17, alignment=ft.MainAxisAlignment.START)



            ],
            spacing=15
        ),
        padding=25,
        width=400
    )

    # Объединяем кнопки в горизонтальный ряд для инженерного режима
    all_buttons = ft.Row(
        controls=[engineering_buttons_area, buttons_area],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=0
    )

    centered_content = ft.Container(
        content=ft.Column(
            controls=[
                top_bar,
                display_area,
                converter_panel,
                all_buttons
            ],
            spacing=0,
        ),
        width=420,
        expand=False,
        alignment=ft.Alignment(0, 0)
    )

    main_layout = ft.Container(
        content=centered_content,
        image=ft.DecorationImage(
            src="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=2564&auto=format&fit=crop",
            fit=ft.BoxFit.COVER,
            opacity=0.08
        ),
        expand=True,
        alignment=ft.Alignment(0, 0)
    )

    async def monitor_tetris(proc):
        while proc.poll() is None:
            await asyncio.sleep(1)
        sarcasm_text.value = "Наигрался? 😏"
        page.update()

    page.on_keyboard_event = on_keyboard
    page.add(ft.Stack(controls=[black_hole_bg, main_layout, custom_drawer], expand=True))
    page.update()

if __name__ == '__main__':
    # run_stress_test()
    ft.run(main)
