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

# --- КОНСТАНТЫ И НАСТРОЙКИ ---
CURRENT_VERSION = "v2.4.2"
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
    "ans": "0"
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
    page.window.height = 800
    page.window.min_width = 400
    page.window.min_height = 800
    page.window.resizable = True
    page.window.center()
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.update()


    def show_update_dialog(latest_version, release_url):
        def close_dialog(e):
            update_dialog.open = False
            page.update()

        def go_to_release(e):
            page.launch_url(release_url)
            update_dialog.open = False
            page.update()

        update_dialog = ft.AlertDialog(
            title=ft.Text("Доступно обновление!"),
            content=ft.Text(f"Вышла новая версия калькулятора: {latest_version}\nУ вас установлена: {CURRENT_VERSION}\n\nХотите скачать обновление сейчас?", color=ft.Colors.WHITE70),
            actions=[
                ft.TextButton("Да, скачать", on_click=go_to_release),
                ft.TextButton("Нет, позже", on_click=close_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor="#1E1E2E"
        )
        page.overlay.append(update_dialog)
        update_dialog.open = True
        page.update()

    def startup_update_check():
        try:
            url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            response = urllib.request.urlopen(req, timeout=3)
            data = json.loads(response.read())
            latest_version = data.get("tag_name")
            release_url = data.get("html_url")
            
            if latest_version and latest_version != CURRENT_VERSION:
                # Need to wait a bit until page is ready
                time.sleep(1)
                page.run_task(lambda: show_update_dialog(latest_version, release_url))
        except Exception:
            pass

    threading.Thread(target=startup_update_check, daemon=True).start()

    def check_for_updates(e=None):
        """Ручная проверка обновлений через GitHub API"""
        page.snack_bar = ft.SnackBar(
            content=ft.Text("Поиск обновлений...", color=COLORS["text_white"]),
            bgcolor=ft.Colors.BLUE_900,
            duration=2000
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
                
                if latest_version and latest_version != CURRENT_VERSION:
                    page.run_task(lambda: show_update_dialog(latest_version, release_url))
                else:
                    def show_latest_snack():
                        page.snack_bar = ft.SnackBar(
                            content=ft.Text(f"У вас актуальная версия ({CURRENT_VERSION})", color=COLORS["text_white"]),
                            bgcolor=ft.Colors.GREEN_800,
                        )
                        page.snack_bar.open = True
                        page.update()
                    page.run_task(show_latest_snack)

            except Exception:
                def show_err_snack():
                    page.snack_bar = ft.SnackBar(
                        content=ft.Text("Ошибка проверки обновлений", color=COLORS["text_white"]),
                        bgcolor=ft.Colors.RED_800,
                        duration=3000
                    )
                    page.snack_bar.open = True
                    page.update()
                page.run_task(show_err_snack)

        threading.Thread(target=run_manual_update_check, daemon=True).start()


    # Состояние приложения
    calc_state = INITIAL_STATE.copy()
    calc_state["history"] = [] # Избегаем общих ссылок


    admin_dialog = ft.AlertDialog(
        title=ft.Text("МОИ СЕКРЕТИКИ 🕵️‍♂️ (v2.4.2)"),
        content=ft.Column([
            ft.Text("--- КЛАССИКА ---", size=12, weight=ft.FontWeight.BOLD, color="#8B5CF6"),
            ft.Text("• 1000 - 7 =", size=13),
            ft.Text("• Результат 300", size=13),
            ft.Text("• 80085", size=13),
            ft.Text("• Деление на ноль", size=13),
            
            ft.Text("--- КУЛЬТУРА ---", size=12, weight=ft.FontWeight.BOLD, color="#F59E0B"),
            ft.Text("• Результат 777", size=13),
            ft.Text("• Результат 0.07", size=13),
            ft.Text("• Результат 88", size=13),
            ft.Text("• 1 + 1 =", size=13),
            ft.Text("• Результат 42", size=13),
            ft.Text("• Результат 1984", size=13),
            
            ft.Text("--- ХАКЕРСКОЕ ---", size=12, weight=ft.FontWeight.BOLD, color="#10B981"),
            ft.Text("• 1337, 228, 322", size=13),
            ft.Text("• Нажать 'C' четыре раза", size=13),
            ft.Text("• Нажать '=' до 16 раз", size=13),
            ft.Text("• Ввести 'admin' или 'секрет'", size=13)
        ], scroll=ft.ScrollMode.AUTO, height=350, spacing=8),
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
    
    sarcasm_text = ft.Text(value="", color=ft.Colors.PURPLE_300, size=14, italic=True, text_align=ft.TextAlign.RIGHT, max_lines=2)

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
        calc_state["history"].append(entry)
        if len(calc_state["history"]) > 3:
            calc_state["history"].pop(0)
        update_history_ui()

    def clear_active_effects():
        """Сбрасывает все активные визуальные эффекты и пасхалки"""
        page.bgcolor = COLORS["bg_main"]
        page.title = "Калькулятор нового поколения"
        current_input.color = COLORS["text_white"]
        black_hole_bg.visible = False
        black_hole_bg.opacity = 0
        sarcasm_text.value = ""
        page.update()

    def update_operator_styles(active_op=""):
        """Обновляет подсветку выбранного оператора (+, -, *, /)"""
        for op, btn in op_btns.items():
            if op not in ["/", "*", "-", "+"]:
                continue
            if op == active_op:
                btn.content.bgcolor = ft.Colors.WHITE
                btn.content.content.color = COLORS["accent_amber"]
                btn.content.shadow.blur_radius = 15
                btn.content.shadow.color = ft.Colors.with_opacity(0.4, COLORS["accent_amber"])
            else:
                btn.content.bgcolor = ft.Colors.TRANSPARENT
                btn.content.content.color = COLORS["text_white"]
                btn.content.shadow.blur_radius = 10
                btn.content.shadow.color = COLORS["neon_purple"]
            btn.content.update()


    # --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ЛОГИКИ ---

    async def run_c4_explosion():
        """Пасхалка: взрыв при 4-х нажатиях на C"""
        calc_state["is_animating"] = True
        for i in range(10):
            page.bgcolor = COLORS["accent_red"] if i % 2 == 0 else ft.Colors.BLACK
            current_input.value = "💥 EXPLOSION 💥" if i < 3 else ("🔥" * (i - 2))
            current_input.size = 24 if i < 3 else 48
            page.update()
            await asyncio.sleep(0.1)
        
        page.bgcolor = COLORS["bg_main"]
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
            await asyncio.sleep(0.04)
        
        if calc_state.get("abort_animation", False):
            current_input.color = COLORS["text_white"]
            current_input.value = "0"
            format_number_scale("0")
            sarcasm_text.value = "Отсчёт прерван."
            calc_state.update({"operand1": "0", "operand2": "", "operator": "", "new_operand": False, "is_animating": False, "abort_animation": False})
        else:
            current_input.value = "Я ГУЛЬ 🩸"
            current_input.size = 56
            page.update()
            await asyncio.sleep(1.5)
            current_input.color = COLORS["text_white"]
            current_input.value = "993"
            sarcasm_text.value = "Я гуль... 1000 - 7 = 993... 🖤"
            calc_state.update({"operand1": "993", "operand2": "", "operator": "", "new_operand": True, "is_animating": False})
        page.update()

    async def run_jackpot_effect():
        """Эффект: Джекпот при 777"""
        calc_state["is_animating"] = True
        for _ in range(10):
             page.bgcolor = ft.Colors.AMBER_400 if page.bgcolor != ft.Colors.AMBER_400 else ft.Colors.BLACK
             page.update()
             await asyncio.sleep(0.08)
        page.bgcolor = COLORS["bg_main"]
        calc_state["is_animating"] = False
        page.update()

    async def run_matrix_mode():
        """Эффект: Режим Матрицы при 1337"""
        clear_active_effects()
        calc_state["is_animating"] = True
        for i in range(10):
            page.bgcolor = "#001A00" if i % 2 == 0 else "#000000"
            current_input.value = "BREACH DETECTED" if i % 2 == 0 else "N E O"
            page.update()
            await asyncio.sleep(0.08)
        
        page.bgcolor = "#050505"
        page.title = "MATRIX_MODE 💀"
        current_input.color = "#00FF41"
        sarcasm_text.value = "С возвращением, Нео. 💀"
        calc_state["is_animating"] = False
        page.update()

    async def run_glitch_division():
        """Эффект: Ошибка сингулярности (деление на ноль)"""
        clear_active_effects()
        calc_state["is_animating"] = True
        for i in range(12):
            page.bgcolor = ft.Colors.RED_900 if i % 2 == 0 else ft.Colors.INDIGO_900
            current_input.value = "CRITICAL_FAILURE" if i % 3 == 0 else "N U L L _ V O I D"
            current_input.size = 20 + (i * 2)
            page.update()
            await asyncio.sleep(0.06)
        
        # Активация черной дыры
        page.bgcolor = "#000000"
        black_hole_bg.visible = True
        black_hole_bg.opacity = 1
        current_input.value = "v o i d"
        current_input.size = 56
        current_input.opacity = 0.5
        sarcasm_text.value = "Сингулярность достигнута. Вернусь через 5 минут. 🌑"
        sarcasm_text.color = ft.Colors.GREY_400
        calc_state.update({"operand1": "0", "operand2": "", "operator": "", "new_operand": True, "is_animating": False})
        page.update()
        
        await asyncio.sleep(300)
        
        if black_hole_bg.visible:
            clear_active_effects()
            sarcasm_text.value = "Вселенная восстановилась. Только больше так не делай."
            sarcasm_text.color = COLORS["accent_purple"]
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
            elif data == "sq2": res = val * val
            
            res_str = f"{res:g}"
            calc_state[target_operand] = res_str
            current_input.value = format_number_scale(res_str)
            sarcasm_text.value = "Научный подход! Математики в чате."
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

    def process_input(data):
        if calc_state.get("is_animating", False):
            if data in ["AC", "C"]:
                calc_state["abort_animation"] = True
            return
        if not data:
            return

        if data != "=":
            calc_state["eq_clicks"] = 0
            
        if data != "C":
            calc_state["c_clicks"] = 0

        # Сброс насмешки только при начале нового ввода чисел или очистке
        if data in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", ".", "AC", "C"] or data.startswith("LETTER_"):
            sarcasm_text.value = ""
            
        if data.startswith("LETTER_"):
            if not zen_active:
                sarcasm_text.value = f"Буква «{data.split('_')[1]}»? Сэр, мы тут математикой занимаемся, а не сочинения пишем!"
            page.update()
            return
        
        if data == "AC":
            calc_state.update({"operand1": "0", "operand2": "", "operator": "", "new_operand": False})
            calc_state["history"].clear()
            current_input.value = "0"
            format_number_scale("0")
            update_history_ui()
            update_operator_styles("")
            clear_active_effects()
            if "=" in op_btns:
                op_btns["="].visible = True
            page.update()
            return

        if data == "C":
            clear_active_effects()
            if "=" in op_btns: op_btns["="].visible = True
            
            calc_state["c_clicks"] += 1
            if calc_state["c_clicks"] == 4:
                page.run_task(run_c4_explosion)
                return
            elif calc_state["c_clicks"] >= 5:
                sarcasm_text.value = "Система и так в руинах, чего ты еще хочешь?"

                
            if calc_state["operator"] == "":
                calc_state["operand1"] = "0"
            else:
                calc_state["operand2"] = ""
            current_input.value = "0"
            format_number_scale("0")
            page.update()
            return
            
        if data == "Ans":
            target_operand = "operand1" if calc_state["operator"] == "" else "operand2"
            calc_state[target_operand] = calc_state["ans"]
            current_input.value = format_number_scale(calc_state[target_operand])
            page.update()
            return

        if data in ["(", ")"]:
            target_operand = "operand1" if calc_state["operator"] == "" else "operand2"
            if calc_state[target_operand] == "0":
                calc_state[target_operand] = data
            else:
                calc_state[target_operand] += data
            current_input.value = format_number_scale(calc_state[target_operand])
            page.update()
            return
        if data == "%":
            target_operand = "operand1" if calc_state["operator"] == "" else "operand2"
            if calc_state[target_operand]:
                try:
                    val = Decimal(calc_state[target_operand]) / Decimal("100")
                    form_val = f"{val:f}"
                    if '.' in form_val: form_val = form_val.rstrip('0').rstrip('.')
                    calc_state[target_operand] = form_val
                    current_input.value = format_number_scale(calc_state[target_operand])
                    page.update()
                except Exception:
                    pass
            return

        if data in ["/", "*", "-", "+", "^"]:
            calc_state["operator"] = data
            calc_state["new_operand"] = True
            update_operator_styles(data)
            return

        # --- Научные функции (Unary) ---
        if data in ["sin", "cos", "tan", "sqrt", "log", "ln", "abs", "fact", "sq2"]:
            target_operand = "operand1" if calc_state["operator"] == "" else "operand2"
            calculate_scientific(data, target_operand)
            return


        if data in ["pi", "e"]:
            target_operand = "operand1" if calc_state["operator"] == "" else "operand2"
            val = str(math.pi) if data == "pi" else str(math.e)
            calc_state[target_operand] = val
            current_input.value = format_number_scale(val)
            page.update()
            return

        if data == "=":
            # Механика поломки кнопки
            calc_state["eq_clicks"] += 1
            if calc_state["eq_clicks"] >= 16:
                 sarcasm_text.value = "Ой... Кнопка улетела в черную дыру. Нажмите AC."
                 current_input.value = "ERR: GONE"
                 if "=" in op_btns:
                     op_btns["="].visible = False
                 page.update()
                 return

            if calc_state["operator"] == "" or calc_state["operand2"] == "":
                if calc_state["eq_clicks"] == 2:
                    current_input.value = format_number_scale(calc_state["operand1"])
                elif calc_state["eq_clicks"] == 4:
                    sarcasm_text.value = f"Знаешь, {calc_state['operand1']} = {calc_state['operand1']}. Удовольствие получено?"
                    page.update()
                elif calc_state["eq_clicks"] == 8:
                    sarcasm_text.value = "Сломать кнопку «равно» — это твой новый челлендж?"
                    page.update()
                return

            if calc_state["operator"] and calc_state["operand2"] != "":
                try:
                    val1 = Decimal(calc_state["operand1"])
                    val2 = Decimal(calc_state["operand2"])
                    res = Decimal(0)
                    
                    if calc_state["operator"] == "+": res = val1 + val2
                    elif calc_state["operator"] == "-": res = val1 - val2
                    elif calc_state["operator"] == "*": res = val1 * val2
                    elif calc_state["operator"] == "/":
                        if val2 == Decimal(0):
                            raise ZeroDivisionError
                        res = val1 / val2
                    elif calc_state["operator"] == "^":
                        res = Decimal(str(pow(float(val1), float(val2))))
                    elif calc_state["operator"] in ["mod", "%"]:
                        res = val1 % val2
                    
                    calc_state["ans"] = str(res)
                    if zen_active:
                        # В режиме Дзен считаем всё тихо
                        pass
                    elif val1 == Decimal("1000") and val2 == Decimal("7") and calc_state["operator"] == "-":
                        page.run_task(run_ghoul_animation)
                        return
                    elif val1 == Decimal("1") and val2 == Decimal("1") and calc_state["operator"] == "+":
                        sarcasm_text.value = "В Океании 1+1 всегда равно 3. Старший Брат следит за тобой. 👁️"
                    elif res == Decimal("777"):
                        sarcasm_text.value = "JACKPOT! 🎰 Иди покупай лотерейный билет."
                        page.run_task(run_jackpot_effect)

                    elif res == Decimal("0.07"):
                        sarcasm_text.value = "Меня зовут Калькулятор. Просто Калькулятор. 🔫🍸"
                    elif res == Decimal("88"):
                        sarcasm_text.value = "88 миль в час? Пора в будущее! ⚡"
                    elif res == Decimal("300"):
                        sarcasm_text.value = "Тракторист? Понимаю, уважаю. 🚜"
                    elif res == Decimal("911"):
                        sarcasm_text.value = "Вызываю службу спасения ваших математических навыков... 🚑"
                    elif res == Decimal("3.14") or res == Decimal("3.14159"):
                        sarcasm_text.value = "С днем Пи! Где мой черничный пирог? 🥧"
                    elif res == Decimal("42"):
                        sarcasm_text.value = "42 — Главный ответ на вопрос Жизни, Вселенной и всего такого."
                    elif res == Decimal("80085"):
                        sarcasm_text.value = "80085? Классика жанра. ( ͡° ͜ʖ ͡°)"
                    elif res == Decimal("5051"):
                        sarcasm_text.value = "5051? Очень по-взрослому."
                    elif res == Decimal("1337"):
                         sarcasm_text.value = "1337... Мы тут все элитные хакеры, да?"
                         page.run_task(run_matrix_mode)

                    elif res == Decimal("228") or val1 == Decimal("228"):
                        sarcasm_text.value = "228? Статья за хранение... калькуляторов."
                    elif res == Decimal("322") or val1 == Decimal("322"):
                        sarcasm_text.value = "322... Кто-то опять решил слить катку (GG)."
                    elif res == Decimal("146") or val1 == Decimal("146"):
                        sarcasm_text.value = "146%? Эту математику одобряет Центризбирком."
                    elif res == Decimal("2007") or val1 == Decimal("2007"):
                        sarcasm_text.value = "Верни мне мой 2007-й... Сентябрь горит, убийца плачет 🥀"
                    elif res == Decimal("1984") or val1 == Decimal("1984"):
                        sarcasm_text.value = "Большой Брат следит за твоими вычислениями."
                    elif res == Decimal("69") or val1 == Decimal("69"):
                        sarcasm_text.value = "69? Nice. ( ͡° ͜ʖ ͡°)"
                    elif res == Decimal("420") or val1 == Decimal("420"):
                        sarcasm_text.value = "420? Время расслабиться... 🌿"
                    elif res == Decimal("256"):
                        sarcasm_text.value = "256! С Днем программиста!"
                    elif res == Decimal("404"):
                        sarcasm_text.value = "Ничего не найдено, зато мы нашли друг друга! ✨"
                    elif res >= Decimal("9000") and res < Decimal("9500"):
                        sarcasm_text.value = "IT'S OVER 9000!!!! 🔥"
                    elif res == Decimal("2048"):
                        sarcasm_text.value = "2048? Собираешься играть в плиточки на калькуляторе?"
                    elif res < Decimal("0"):
                        sarcasm_text.value = "Ушли в минус. Жизненно, как мой банковский счет."
                    elif res == Decimal("314"):
                        sarcasm_text.value = "Похоже на Пи. Пирога захотелось."
                    elif res > Decimal("1000000000000"):
                        sarcasm_text.value = "Ого, да ты прям магнат цифр."
                    elif res == Decimal("13"):
                        sarcasm_text.value = "13... Плохое число... Не рекомендую."

                    # Форматирование результата (избавляемся от научной нотации типа 9E+3)
                    res_str = f"{res:f}"
                    if '.' in res_str:
                         res_str = res_str.rstrip('0').rstrip('.')
                    
                    op_sign = {"/": "÷", "*": "×", "-": "-", "+": "+", "^": "^"}[calc_state['operator']]
                    hist_entry = f"{calc_state['operand1']} {op_sign} {calc_state['operand2']} = {res_str}"
                    add_history(hist_entry)
                    
                    calc_state.update({"operand1": res_str, "operand2": "", "operator": "", "new_operand": True})
                    current_input.value = format_number_scale(res_str)
                    update_operator_styles("")
                    
                except ZeroDivisionError:
                    page.run_task(run_glitch_division)
                    return
                except Exception:
                    # Попытка вычислить как выражение (для скобок)
                    try:
                        expr = f"{calc_state['operand1']}{calc_state['operator']}{calc_state['operand2']}"
                        expr = expr.replace("×", "*").replace("÷", "/")
                        import math
                        safe_dict = {"math": math, "sin": math.sin, "cos": math.cos, "tan": math.tan, "sqrt": math.sqrt, "log": math.log10, "ln": math.log, "pi": math.pi, "e": math.e}
                        res_val = eval(expr, {"__builtins__": None}, safe_dict)
                        res_str = f"{res_val:g}"
                        calc_state["ans"] = res_str
                        calc_state.update({"operand1": res_str, "operand2": "", "operator": "", "new_operand": True})
                        current_input.value = format_number_scale(res_str)
                    except:
                        current_input.value = "Ошибка вычисления"
                        current_input.size = 24
                        calc_state.update({"operand1": "0", "operand2": "", "operator": "", "new_operand": True})
            page.update()
            return

        # Обработка ввода цифр и запятой
        if calc_state["operator"] == "":
            target_operand = "operand1"
        else:
            target_operand = "operand2"

        if calc_state["new_operand"]:
            calc_state[target_operand] = data if data != "." else "0."
            calc_state["new_operand"] = False
            if target_operand == "operand2":
                 update_operator_styles("")
        else:
            if data == ".":
                if "." not in calc_state[target_operand]:
                    calc_state[target_operand] += "." if calc_state[target_operand] else "0."
            else:
                if calc_state[target_operand] == "0":
                    calc_state[target_operand] = data
                else:
                    calc_state[target_operand] += data

        current_input.value = format_number_scale(calc_state[target_operand])
        page.update()

    def on_button_click(e):
        process_input(e.control.data)

    def on_keyboard(e):
        if custom_drawer.left == 0:
            return  # Игнорировать клавиатуру, когда боковое меню открыто
        key = e.key
        
        calc_state["key_buffer"] += key.lower()
        calc_state["key_buffer"] = calc_state["key_buffer"][-10:]
        if any(kw in calc_state["key_buffer"] for kw in ["admin", "фвьшт", "секрет", "ctrhtn"]):
            calc_state["key_buffer"] = ""
            admin_dialog.open = True
            page.update()
            return
        
        # Пасхалка на буквы
        if len(key) == 1 and key.isalpha() and key.isascii():
            process_input("LETTER_" + key)
            return
            
        if key in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", ".", "+", "-", "*", "/", "%"]:
            process_input(key)
        elif key in ["Enter", "Numpad Enter", "="]:
            process_input("=")
        elif key == "Escape":
            process_input("AC")
        elif key in ["Backspace", "Delete"]:
            process_input("C")

    page.on_keyboard_event = on_keyboard

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
    
    def toggle_zen(e):
        nonlocal zen_active
        zen_active = not zen_active
        if zen_active:
             history_container.opacity = 0
             drawer_btn.opacity = 0
             drawer_btn.disabled = True
             zen_btn.icon = ft.Icons.SELF_IMPROVEMENT
             zen_btn.icon_color = "#8B5CF6"
        else:
             history_container.opacity = 1
             drawer_btn.opacity = 1
             drawer_btn.disabled = False
             zen_btn.icon = ft.Icons.SELF_IMPROVEMENT_OUTLINED
             zen_btn.icon_color = ft.Colors.WHITE54
        page.update()

    def toggle_engineering(e, force_state=None):
        if force_state is not None:
            calc_state["is_engineering"] = force_state
        else:
            calc_state["is_engineering"] = not calc_state["is_engineering"]
        
        if calc_state["is_engineering"]:
            engineering_buttons_area.visible = True
            centered_content.width = 750
            page.window.width = 800
            # eng_btn_drawer.text = "Выключить Инженерный режим" # Drawer button removed
            science_btn.icon = ft.Icons.SCIENCE
            science_btn.icon_color = "#F59E0B"
        else:
            engineering_buttons_area.visible = False
            centered_content.width = 420
            page.window.width = 420
            # eng_btn_drawer.text = "Включить Инженерный режим" # Drawer button removed
            science_btn.icon = ft.Icons.SCIENCE_OUTLINED
            science_btn.icon_color = ft.Colors.WHITE54
        
        # Обновляем фон черной дыры, если он активен
        if black_hole_bg.visible:
            page.update()
            
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

    top_bar = ft.Container(
        content=ft.Row(
            controls=[
                drawer_btn,
                ft.Row([science_btn, zen_btn], spacing=0)
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=ft.Padding(left=10, right=10, top=10, bottom=0)
    )

    # --- UI КОМПОНЕНТЫ ---

    def create_display_area():
        """Создает область экрана калькулятора"""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Column(
                            controls=history_texts, 
                            spacing=2, 
                            alignment=ft.MainAxisAlignment.END,
                            horizontal_alignment=ft.CrossAxisAlignment.END,
                            scroll=ft.ScrollMode.HIDDEN
                        ),
                        height=90,
                    ),
                    ft.Container(
                        content=sarcasm_text,
                        height=45,
                        alignment=ft.Alignment.TOP_RIGHT,
                    ),
                    current_input
                ],
                alignment=ft.MainAxisAlignment.END,
                horizontal_alignment=ft.CrossAxisAlignment.END,
                spacing=0
            ),
            padding=ft.Padding(25, 0, 25, 20),
            height=245,
            alignment=ft.Alignment.BOTTOM_RIGHT
        )

    def create_converter_drawer():
        """Создает боковую панель с конвертером"""
        exchange_rates = {"USD": 95.0, "EUR": 105.0, "GEL": 35.0}
        try:
            req = urllib.request.urlopen("https://api.exchangerate-api.com/v4/latest/RUB", timeout=2)
            data = json.loads(req.read())
            rates = data.get("rates", {})
            if "USD" in rates:
                exchange_rates["USD"] = 1 / rates["USD"]
                exchange_rates["EUR"] = 1 / rates["EUR"]
                exchange_rates["GEL"] = 1 / rates["GEL"]
        except: pass

        def convert_values(e):
            try:
                val = Decimal(conv_input.value.replace(",", "."))
                usd = val / Decimal(str(round(exchange_rates["USD"], 4)))
                gel = val / Decimal(str(round(exchange_rates["GEL"], 4)))
                eur = val / Decimal(str(round(exchange_rates["EUR"], 4)))
                conv_curr.value = f"＄ {usd:.2f} USD\n€ {eur:.2f} EUR\n₾ {gel:.2f} GEL"
                
                lbs = val * Decimal("2.20462")
                oz = val * Decimal("35.274")
                conv_weight.value = f"⚖️  {lbs:.2f} фунтов\n⚖️  {oz:.2f} унций"
                
                feet = val * Decimal("3.28084")
                cm = val * Decimal("100")
                conv_length.value = f"📏  {feet:.2f} футов\n📏  {cm:.2f} см"
            except:
                conv_curr.value = "..."; conv_weight.value = "..."; conv_length.value = "..."
            page.update()

        conv_input = ft.TextField(
            label="Сумма / Вес / Длина (RUB/KG/M)", 
            on_change=convert_values, color=COLORS["text_white"], 
            border_color=COLORS["accent_purple"], cursor_color=COLORS["accent_purple"]
        )
        conv_curr = ft.Text("...", size=16, color=COLORS["text_white"], weight=ft.FontWeight.W_500)
        conv_weight = ft.Text("...", size=16, color=COLORS["text_white"], weight=ft.FontWeight.W_500)
        conv_length = ft.Text("...", size=16, color=COLORS["text_white"], weight=ft.FontWeight.W_500)

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row([
                        ft.Text("Меню / Конвертер", size=20, weight=ft.FontWeight.W_600, color=COLORS["accent_purple"]),
                        ft.IconButton(icon=ft.Icons.CLOSE, on_click=lambda _: close_drawer(), icon_color=COLORS["text_dim"])
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Divider(color=ft.Colors.WHITE24),
                    conv_input,
                    ft.Container(height=10),
                    ft.Text("Валюты (USD/EUR/GEL):", color=COLORS["text_dim"], size=13),
                    conv_curr,
                    ft.Text("Вес (Фунт/Унция):", color=COLORS["text_dim"], size=13),
                    conv_weight,
                    ft.Text("Длина (Фут/СМ):", color=COLORS["text_dim"], size=13),
                    conv_length,
                    ft.Divider(color=ft.Colors.WHITE24),
                    ft.TextButton("Telegram", icon=ft.Icons.SEND, url="https://t.me/JoeMoeCode"),
                    ft.TextButton("Обновить", icon=ft.Icons.REFRESH, on_click=check_for_updates),
                    ft.Text("Версия: " + CURRENT_VERSION, color=COLORS["text_dim"], size=12)
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


    # --- Инженерные кнопки ---
    engineering_buttons_area = ft.Container(
        content=ft.Column(
            controls=[
                ft.Row([
                    create_btn("sin", font_size=18), 
                    create_btn("cos", font_size=18), 
                    create_btn("tan", font_size=18),
                    create_btn("xʸ", "^", font_size=18)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([
                    create_btn("√", "sqrt", font_size=18), 
                    create_btn("log", font_size=18), 
                    create_btn("ln", font_size=18),
                    create_btn("x²", "sq2", font_size=18)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([
                    create_btn("abs", font_size=18), 
                    create_btn("n!", "fact", font_size=18), 
                    create_btn("(", "(", color="#10B981", font_size=20),
                    create_btn(")", ")", color="#10B981", font_size=20)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([
                    create_btn("π", "pi", font_size=24),
                    create_btn("e", font_size=24),
                    create_btn("Ans", "Ans", color="#3B82F6", font_size=16),
                    create_btn("mod", "%", font_size=16)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ],
            spacing=15
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
                    create_btn("=", "=", color=COLORS["text_white"], bgcolor=COLORS["accent_blue"], is_neon=True)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

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

    page.add(ft.Stack(controls=[black_hole_bg, main_layout, custom_drawer], expand=True))
    page.update()

if __name__ == '__main__':
    # run_stress_test()
    ft.run(main)
