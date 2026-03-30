import flet as ft
from decimal import Decimal, InvalidOperation
import time
import asyncio
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
        ("5", "*", "2"), ("100", "/", "10")
    ]
    success_count = 0
    for i, (a, op, b) in enumerate(operations):
        try:
            da, db = Decimal(a), Decimal(b)
            if op == '+': res = da + db
            elif op == '-': res = da - db
            elif op == '*': res = da * db
            elif op == '/': 
                if db == Decimal(0):
                    res = "Деление на ноль невозможно"
                else:
                    res = da / db
            print(f"[{i+1}/20] Успех: {a} {op} {b} = {res}")
            success_count += 1
        except Exception as e:
            print(f"[{i+1}/20] Ошибка: {e}")
    print(f"--- Тест завершен: {success_count}/20 операций выполнено успешно ---")


def main(page: ft.Page):
    page.title = "Калькулятор нового поколения"
    page.bgcolor = "#0B0E14"  # Deep Charcoal / Midnight Blue
    page.window.width = 400
    page.window.height = 840
    page.window.resizable = True
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0

    import threading

    # Состояние приложения
    calc_state = {
        "operand1": "0",
        "operand2": "",
        "operator": "",
        "new_operand": False,
        "history": [],
        "eq_clicks": 0,
        "c_clicks": 0,
        "key_buffer": "",
        "is_animating": False
    }

    admin_dialog = ft.AlertDialog(
        title=ft.Text("МОЙ СЕКРЕТИК 🌻 (Никому не рассказывать!)"),
        content=ft.Column([
            ft.Text("Попробуйте найти секреты, вводя эти комбинации:", size=14, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE70),
            ft.Text("1000 - 7 =", size=14),
            ft.Text("Результат 300", size=14),
            ft.Text("80085", size=14),
            ft.Text("1337, 228, 322, 146, 2007", size=14),
            ft.Text("1984, 69, 420, 256", size=14),
            ft.Text("404, 2048, 5051", size=14),
            ft.Text("Очень большое число (>9000)", size=14),
            ft.Text("Любая английская буква с клавиатуры", size=14),
            ft.Text("Деление на ноль", size=14),
            ft.Text("Нажать кнопку С четыре раза подряд", size=14),
            ft.Text("Жать подряд знак = (до 8 раз)", size=14)
        ], scroll=ft.ScrollMode.AUTO, height=320, spacing=10),
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
    
    sarcasm_text = ft.Text(value="", color=ft.Colors.PURPLE_300, size=14, italic=True, text_align=ft.TextAlign.RIGHT)

    def update_history_ui():
        for i in range(3):
            if i < len(calc_state["history"]):
                history_texts[2-i].value = calc_state["history"][-(i+1)]
            else:
                history_texts[2-i].value = ""
        page.update()

    def add_history(entry):
        calc_state["history"].append(entry)
        if len(calc_state["history"]) > 3:
            calc_state["history"].pop(0)
        update_history_ui()

    op_btns = {}
    
    def update_operator_styles(active_op=""):
        for op, btn in op_btns.items():
            if op == active_op:
                btn.content.bgcolor = ft.Colors.WHITE
                btn.content.content.color = "#F59E0B"
                btn.content.shadow.blur_radius = 20
                btn.content.shadow.color = ft.Colors.with_opacity(0.5, "#F59E0B")
            else:
                btn.content.bgcolor = ft.Colors.TRANSPARENT
                btn.content.content.color = ft.Colors.WHITE
                btn.content.shadow.blur_radius = 15
                btn.content.shadow.color = "#9333EA"
            btn.content.update()

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
            page.update()
            return

        if data == "C":
            calc_state["c_clicks"] += 1
            if calc_state["c_clicks"] == 4:
                async def explode():
                    import os
                    calc_state["is_animating"] = True
                    for i in range(14):
                        page.bgcolor = ft.Colors.RED if i % 2 == 0 else ft.Colors.BLACK
                        current_input.value = "💥 Взрывчатка С4 активирована 💥" if i < 4 else ("💥" * min(i - 3, 5))
                        current_input.size = 20 if i < 4 else 60
                        page.update()
                        await asyncio.sleep(0.15)
                    os._exit(0)
                page.run_task(explode)
                return
            elif calc_state["c_clicks"] >= 5:
                sarcasm_text.value = "Поздно, он уже взорвался..."
                
            if calc_state["operator"] == "":
                calc_state["operand1"] = "0"
            else:
                calc_state["operand2"] = ""
            current_input.value = "0"
            format_number_scale("0")
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

        if data in ["/", "*", "-", "+"]:
            calc_state["operator"] = data
            calc_state["new_operand"] = True
            update_operator_styles(data)
            return

        if data == "=":
            if calc_state["operator"] == "" or calc_state["operand2"] == "":
                calc_state["eq_clicks"] += 1
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
                    
                    # Генерация насмешки
                    if val1 == Decimal("1000") and val2 == Decimal("7") and calc_state["operator"] == "-":
                        async def ghoul_countdown():
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
                                current_input.color = ft.Colors.WHITE
                                current_input.value = "0"
                                format_number_scale("0")
                                sarcasm_text.value = "Отсчёт прерван."
                                calc_state.update({"operand1": "0", "operand2": "", "operator": "", "new_operand": False, "is_animating": False, "abort_animation": False})
                            else:
                                current_input.value = "Я ГУЛЬ 🩸"
                                current_input.size = 56
                                page.update()
                                await asyncio.sleep(1.5)
                                current_input.color = ft.Colors.WHITE
                                current_input.value = "993"
                                sarcasm_text.value = "Я гуль... 1000 - 7 = 993... 🖤"
                                calc_state.update({"operand1": "993", "operand2": "", "operator": "", "new_operand": True, "is_animating": False})
                            
                            page.update()
                        page.run_task(ghoul_countdown)
                        return
                    elif res == Decimal("300"):
                        sarcasm_text.value = "Тракторист?"
                    elif val1 == Decimal("666") or val2 == Decimal("666") or res == Decimal("666"):
                        sarcasm_text.value = "Я калькулятор, а не доска Уиджи. Больше так не делай."
                    elif val1 == Decimal("777") or val2 == Decimal("777") or res == Decimal("777"):
                        sarcasm_text.value = "Джекпот! 🎰 Иди покупай лотерейный билет."
                    elif val1 == Decimal("2") and val2 == Decimal("2") and calc_state["operator"] == "*":
                        sarcasm_text.value = "Дважды два? Серьезно? Давай еще 1+1 посчитаем."
                    elif val1 == Decimal("0") and val2 == Decimal("0") and calc_state["operator"] in ["+", "-"]:
                        sarcasm_text.value = "0 + 0? Вау, ты просто превзошел сам себя."
                    elif val1 == val2 and calc_state["operator"] == "-":
                        sarcasm_text.value = "Вычитаешь сам из себя? Получишь ноль, я гарантирую."
                    elif val2 == Decimal("0") and calc_state["operator"] in ["+", "-"]:
                        sarcasm_text.value = "Прибавляешь ноль? Эффектность 100 уровня."
                    elif val2 == Decimal("1") and calc_state["operator"] in ["*", "/"]:
                        sarcasm_text.value = "Умножение или деление на 1... Мощный мозг."
                    elif res == Decimal("42"):
                        sarcasm_text.value = "42 — Главный ответ на вопрос Жизни, Вселенной и всего такого."
                    elif res == Decimal("80085"):
                        sarcasm_text.value = "80085? Классика жанра. ( ͡° ͜ʖ ͡°)"
                    elif res == Decimal("5051"):
                        sarcasm_text.value = "5051? Очень по-взрослому."
                    elif res == Decimal("1337"):
                        sarcasm_text.value = "1337... Мы тут все элитные хакеры, да?"
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
                        sarcasm_text.value = "Ошибка 404: Смысл жизни не найден."
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
                    
                    op_sign = {"/": "÷", "*": "×", "-": "-", "+": "+"}[calc_state['operator']]
                    hist_entry = f"{calc_state['operand1']} {op_sign} {calc_state['operand2']} = {res_str}"
                    add_history(hist_entry)
                    
                    calc_state.update({"operand1": res_str, "operand2": "", "operator": "", "new_operand": True})
                    current_input.value = format_number_scale(res_str)
                    update_operator_styles("")
                    
                except ZeroDivisionError:
                    current_input.value = "Деление на ноль: Вселенная схлопывается 💥"
                    current_input.size = 20
                    sarcasm_text.value = "Поздравляю, ты создал черную дыру. Спасибо."
                    calc_state.update({"operand1": "0", "operand2": "", "operator": "", "new_operand": True})
                except Exception:
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

    def create_btn(text, data=None, color=ft.Colors.WHITE, is_neon=False, is_gradient=False, width=75, bgcolor=None):
        if data is None: data = text
        
        # Если фон не задан, используем полупрозрачный (Glassmorphism) или прозрачный для неона
        final_bgcolor = bgcolor if bgcolor else (ft.Colors.TRANSPARENT if is_neon else ft.Colors.with_opacity(0.05, ft.Colors.WHITE))
        shadow_color = "#9333EA" if is_neon else ft.Colors.BLACK26
        
        content = ft.Container(
            content=ft.Text(text, size=28, color=color, weight=ft.FontWeight.W_400),
            alignment=ft.Alignment.CENTER,
            width=width,
            height=75,
            border_radius=25,
            bgcolor=final_bgcolor,
            blur=ft.Blur(10, 10, ft.BlurTileMode.CLAMP) if not bgcolor else None,
            border=ft.Border.all(1, ft.Colors.with_opacity(0.1, ft.Colors.WHITE)) if not bgcolor else None,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=15 if is_neon else 5,
                color=shadow_color if is_neon else ft.Colors.with_opacity(0.2, ft.Colors.BLACK),
                offset=ft.Offset(0, 4)
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
        if data in ["/", "*", "-", "+"]:
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

    zen_btn = ft.IconButton(
        icon=ft.Icons.SELF_IMPROVEMENT_OUTLINED, 
        icon_color=ft.Colors.WHITE54,
        on_click=toggle_zen,
        tooltip="Режим Дзен"
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
            controls=[drawer_btn, zen_btn],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=ft.Padding(left=10, right=10, top=10, bottom=0)
    )

    history_container = ft.Column(
        controls=history_texts,
        alignment=ft.MainAxisAlignment.END,
        horizontal_alignment=ft.CrossAxisAlignment.END,
        spacing=4
    )
    
    display_area = ft.Container(
        content=ft.Column(
            controls=[
                history_container,
                ft.Container(height=5),
                sarcasm_text,
                ft.Container(height=5),
                current_input
            ],
            alignment=ft.MainAxisAlignment.END,
            horizontal_alignment=ft.CrossAxisAlignment.END
        ),
        padding=25,
        height=260,
        alignment=ft.Alignment.BOTTOM_RIGHT
    )

    # --- Умный Конвертер (Custom Drawer) ---
    exchange_rates = {"USD": 95.0, "EUR": 105.0, "GEL": 35.0} # Запасные варианты
    try:
        import urllib.request
        import json
        req = urllib.request.urlopen("https://api.exchangerate-api.com/v4/latest/RUB", timeout=2)
        data = json.loads(req.read())
        rates = data.get("rates", {})
        if "USD" in rates:
            exchange_rates["USD"] = 1 / rates["USD"]
            exchange_rates["EUR"] = 1 / rates["EUR"]
            exchange_rates["GEL"] = 1 / rates["GEL"]
    except Exception:
        pass

    def convert_values(e):
        try:
            val = Decimal(conv_input.value.replace(",", "."))
            # Валюты 
            usd = val / Decimal(str(round(exchange_rates["USD"], 4)))
            gel = val / Decimal(str(round(exchange_rates["GEL"], 4)))
            eur = val / Decimal(str(round(exchange_rates["EUR"], 4)))
            conv_curr.value = f"＄ {usd:.2f} USD\n€ {eur:.2f} EUR\n₾ {gel:.2f} GEL"
            
            # Вес
            lbs = val * Decimal("2.20462")
            oz = val * Decimal("35.274")
            conv_weight.value = f"⚖️  {lbs:.2f} фунтов\n⚖️  {oz:.2f} унций"
            
            # Длина
            feet = val * Decimal("3.28084")
            cm = val * Decimal("100")
            conv_length.value = f"📏  {feet:.2f} футов\n📏  {cm:.2f} см"
        except:
            conv_curr.value = "..."
            conv_weight.value = "..."
            conv_length.value = "..."
        finally:
            page.update()

    conv_input = ft.TextField(
        label="Введите сумму / вес / длину...", 
        on_change=convert_values, 
        color=ft.Colors.WHITE, 
        border_color="#8B5CF6",
        focused_border_color="#3B82F6",
        cursor_color="#8B5CF6"
    )
    conv_curr = ft.Text("...", size=16, color=ft.Colors.WHITE, weight=ft.FontWeight.W_500)
    conv_weight = ft.Text("...", size=16, color=ft.Colors.WHITE, weight=ft.FontWeight.W_500)
    conv_length = ft.Text("...", size=16, color=ft.Colors.WHITE, weight=ft.FontWeight.W_500)

    def close_custom_drawer(e):
        custom_drawer.left = -400
        page.update()

    custom_drawer_content = ft.Container(
        content=ft.Column(
            controls=[
                ft.Row([
                    ft.Text("Конвертер", size=22, weight=ft.FontWeight.W_600, color="#8B5CF6"),
                    ft.IconButton(icon=ft.Icons.CLOSE, on_click=close_custom_drawer, icon_color=ft.Colors.WHITE54)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(color=ft.Colors.WHITE24),
                ft.Container(height=5),
                conv_input,
                ft.Container(height=15),
                ft.Text("Валюты (Покупка за RUB):", color=ft.Colors.WHITE54, size=14),
                conv_curr,
                ft.Container(height=15),
                ft.Text("Вес (Из килограммов):", color=ft.Colors.WHITE54, size=14),
                conv_weight,
                ft.Container(height=15),
                ft.Text("Длина (Из метров):", color=ft.Colors.WHITE54, size=14),
                conv_length,
                ft.Divider(color=ft.Colors.WHITE24),
                ft.Text("Полезные ссылки:", color=ft.Colors.WHITE54, size=14),
                ft.TextButton(
                    content=ft.Row([ft.Icon(ft.Icons.TELEGRAM, size=20, color=ft.Colors.BLUE_400), ft.Text("Наш Telegram", color=ft.Colors.BLUE_400)]),
                    url="https://t.me/placeholder"
                ),
                ft.TextButton(
                    content=ft.Row([ft.Icon(ft.Icons.BUG_REPORT, size=20, color=ft.Colors.RED_400), ft.Text("Сообщить о баге", color=ft.Colors.RED_400)]),
                    url="https://github.com/placeholder/issues"
                )
            ]
        ),
        padding=ft.Padding(15, 20, 15, 20)
    )

    custom_drawer = ft.Container(
        content=custom_drawer_content,
        left=-400,
        top=0,
        bottom=0,
        width=320,
        bgcolor="#121620",
        animate_position=400,
        shadow=ft.BoxShadow(spread_radius=10, blur_radius=50, color=ft.Colors.BLACK54)
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
                    create_btn("=", "=", color=ft.Colors.WHITE, bgcolor="#3B82F6")
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ],
            spacing=15
        ),
        padding=25,
        expand=True
    )

    main_layout = ft.Container(
        content=ft.Column(
            controls=[
                top_bar,
                display_area,
                buttons_area
            ]
        ),
        image=ft.DecorationImage(
            src="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=2564&auto=format&fit=crop",
            fit=ft.BoxFit.COVER,
            opacity=0.08
        ),
        expand=True,
    )

    page.add(ft.Stack(controls=[main_layout, custom_drawer], expand=True))

if __name__ == '__main__':
    # run_stress_test()
    ft.run(main)
