import flet as ft
import asyncio
import random
import sys

# Цветовая палитра калькулятора (v3.0.0)
COLORS = {
    "bg": "#0B0E14",
    "overlay_bg": "#1A1D23",
    "border": "#8B5CF6",
    "text": "#F59E0B",
    "win_text": "#10B981",
    "loss_text": "#F87171",
    "blocks": ["#8B5CF6", "#F59E0B", "#10B981", "#3B82F6", "#F87171", "#9333EA", "#EC4899"]
}

BOARD_WIDTH = 10
BOARD_HEIGHT = 20
WIN_SCORE = 9999

# Фигуры тетриса
SHAPES = [
    [[1, 1, 1, 1]], # I
    [[1, 1], [1, 1]], # O
    [[1, 1, 1], [0, 1, 0]], # T
    [[1, 1, 1], [1, 0, 0]], # L
    [[1, 1, 1], [0, 0, 1]], # J
    [[0, 1, 1], [1, 1, 0]], # S
    [[1, 1, 0], [0, 1, 1]]  # Z
]

class TetrisGame:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "PURPURIKI TETRIS v3.0.0"
        self.page.bgcolor = COLORS["bg"]
        self.page.window.width = 450
        self.page.window.height = 920
        self.page.window.resizable = False
        self.page.window.always_on_top = True
        
        self.board = [[None for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]
        self.current_piece = None
        self.current_pos = [0, 0]
        self.score = 0
        self.game_over = False
        self.game_won = False
        self.infinite_mode = False
        self.paused = False
        
        # Основной HUD
        self.score_text = ft.Text(f"SCORE: {self.score}", size=28, color=COLORS["text"], weight=ft.FontWeight.BOLD)
        self.progress_bar = ft.ProgressBar(
            value=0, 
            width=340, 
            color="#10B981", 
            bgcolor="#1E1E2E",
            border_radius=5
        )
        
        # Игровая сетка
        self.grid = ft.Column(
            spacing=2,
            tight=True,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
        
        # Оверлей паузы
        self.pause_overlay = ft.Container(
            content=ft.Text("ПАУЗА", size=48, color=COLORS["text"], weight=ft.FontWeight.BOLD),
            visible=False,
            bgcolor=ft.Colors.with_opacity(0.4, ft.Colors.BLACK),
            alignment=ft.Alignment(0, 0),
            expand=True
        )
        
        # Кастомный оверлей Меню (вместо AlertDialog)
        self.menu_title = ft.Text("", size=32, weight=ft.FontWeight.BOLD, color=COLORS["text"])
        self.menu_subtitle = ft.Text("", size=18, color=ft.Colors.WHITE70)
        self.menu_buttons_container = ft.Row(spacing=10, alignment=ft.MainAxisAlignment.CENTER)
        
        self.menu_overlay = ft.Container(
            content=ft.Container(
                content=ft.Column([
                    self.menu_title,
                    self.menu_subtitle,
                    ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                    self.menu_buttons_container
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True, spacing=10),
                bgcolor=COLORS["overlay_bg"],
                padding=30,
                border_radius=20,
                border=ft.Border.all(2, COLORS["border"]),
                shadow=ft.BoxShadow(blur_radius=50, color=ft.Colors.BLACK),
            ),
            visible=False,
            bgcolor=ft.Colors.with_opacity(0.7, ft.Colors.BLACK),
            alignment=ft.Alignment(0, 0),
            expand=True
        )

        # Основной контейнер игры (Stack)
        self.main_stack = ft.Stack([
            # Слой 0: Игра
                ft.Container(
                    content=ft.Column([
                        self.score_text,
                    self.progress_bar,
                    ft.Container(
                        content=self.grid,
                        width=340, 
                        height=670, 
                        bgcolor="#050505",
                        border=ft.Border.all(1, COLORS["border"]),
                        padding=5,
                        alignment=ft.Alignment(0, 0),
                        border_radius=5
                    ),
                    ft.Text("WASD / ARROWS / NUMPAD | ESC: PAUSE", size=10, color=ft.Colors.WHITE24)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10, scroll=ft.ScrollMode.HIDDEN),
                padding=20,
                alignment=ft.Alignment(0, 0),
                expand=True
            ),
            # Слой 1: Пауза
            self.pause_overlay,
            # Слой 2: Меню
            self.menu_overlay
        ], expand=True)

        self.page.add(self.main_stack)
        self.page.on_keyboard_event = self.handle_keyboard
        self.init_cells()
        self.new_piece()
        self.page.run_task(self.game_loop)

    def init_cells(self):
        self.cells = []
        self.grid.controls.clear()
        for r in range(BOARD_HEIGHT):
            row_controls = []
            for _ in range(BOARD_WIDTH):
                cell = ft.Container(
                    width=30, 
                    height=30, 
                    bgcolor=ft.Colors.with_opacity(0.04, ft.Colors.WHITE), 
                    border_radius=2
                )
                self.cells.append(cell)
                row_controls.append(cell)
            self.grid.controls.append(ft.Row(
                controls=row_controls,
                spacing=2,
                tight=True,
                alignment=ft.MainAxisAlignment.CENTER
            ))

    def new_piece(self):
        self.current_piece = random.choice(SHAPES)
        self.current_color = random.choice(COLORS["blocks"])
        self.current_pos = [0, BOARD_WIDTH // 2 - len(self.current_piece[0]) // 2]
        
        if self.check_collision(self.current_pos, self.current_piece):
            self.game_over = True
            self.show_menu(False)

    def check_collision(self, pos, piece):
        for r, row in enumerate(piece):
            for c, val in enumerate(row):
                if val:
                    new_r, new_c = pos[0] + r, pos[1] + c
                    if (new_r >= BOARD_HEIGHT or new_c < 0 or new_c >= BOARD_WIDTH or 
                        (new_r >= 0 and self.board[new_r][new_c])):
                        return True
        return False

    def rotate_piece(self):
        new_piece = list(zip(*self.current_piece[::-1]))
        if not self.check_collision(self.current_pos, new_piece):
            self.current_piece = new_piece

    def lock_piece(self):
        for r, row in enumerate(self.current_piece):
            for c, val in enumerate(row):
                if val:
                    if 0 <= self.current_pos[0] + r < BOARD_HEIGHT:
                        self.board[self.current_pos[0] + r][self.current_pos[1] + c] = self.current_color
        
        self.clear_lines()
        if not self.game_over and not self.game_won:
            self.new_piece()

    def clear_lines(self):
        lines_to_clear = [i for i, row in enumerate(self.board) if all(row)]
        for i in lines_to_clear:
            self.board.pop(i)
            self.board.insert(0, [None for _ in range(BOARD_WIDTH)])
            self.score += 100
            
        self.score_text.value = f"SCORE: {self.score}"
        
        if not self.infinite_mode:
            self.progress_bar.value = self.score / WIN_SCORE
            
    def show_menu(self, is_win):
        self.paused = True
        # Делаем кнопки компактнее, чтобы текст не дробился
        btn_style = ft.ButtonStyle(
            bgcolor=COLORS["border"],
            color="white",
            padding=0,
            shape=ft.RoundedRectangleBorder(radius=10),
            text_style=ft.TextStyle(size=12, weight=ft.FontWeight.W_500)
        )
        
        common_width = 110
        common_height = 36
        
        if is_win:
            self.menu_title.value = "ПОЗДРАВЛЯЮ!"
            self.menu_title.color = COLORS["win_text"]
            self.menu_subtitle.value = "Вы прошли игру"
            self.menu_buttons_container.controls = [
                ft.FilledButton("Продолжить", on_click=self.continue_infinite, style=btn_style, width=common_width, height=common_height),
                ft.FilledButton("Повторить", on_click=self.reset_game, style=btn_style, width=common_width, height=common_height),
                ft.FilledButton("Выйти", on_click=self.handle_exit, style=btn_style, width=common_width, height=common_height)
            ]
        else:
            self.menu_title.value = "GAME OVER!"
            self.menu_title.color = COLORS["loss_text"]
            self.menu_subtitle.value = "Попробуйте еще раз"
            self.menu_buttons_container.controls = [
                ft.FilledButton("Повторить", on_click=self.reset_game, style=btn_style, width=common_width, height=common_height),
                ft.FilledButton("Выйти", on_click=self.handle_exit, style=btn_style, width=common_width, height=common_height)
            ]
        
        self.menu_overlay.visible = True
        self.page.update()

    async def handle_exit(self, e):
        import sys
        import asyncio
        try:
            # Принудительно проверяем наличие асинхронного метода
            if hasattr(self.page.window, "close_async"):
                await self.page.window.close_async()
            else:
                res = self.page.window.close()
                if asyncio.iscoroutine(res):
                    await res
        except:
            sys.exit()

    def reset_game(self, e=None):
        self.board = [[None for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]
        self.score = 0
        self.game_over = False
        self.game_won = False
        self.infinite_mode = False
        self.paused = False
        self.pause_overlay.visible = False
        self.menu_overlay.visible = False
        self.progress_bar.value = 0
        self.progress_bar.visible = True
        self.score_text.value = f"SCORE: {self.score}"
        self.new_piece()
        self.update_ui()

    def continue_infinite(self, e=None):
        self.infinite_mode = True
        self.game_won = False
        self.paused = False
        self.progress_bar.visible = False
        self.menu_overlay.visible = False
        self.update_ui()

    def update_ui(self):
        try:
            for r in range(BOARD_HEIGHT):
                for c in range(BOARD_WIDTH):
                    color = self.board[r][c] or ft.Colors.with_opacity(0.04, ft.Colors.WHITE)
                    self.cells[r * BOARD_WIDTH + c].bgcolor = color

            if self.current_piece and not self.game_over and not self.game_won:
                for r, row in enumerate(self.current_piece):
                    for c, val in enumerate(row):
                        if val:
                            idx = (self.current_pos[0] + r) * BOARD_WIDTH + (self.current_pos[1] + c)
                            if 0 <= idx < len(self.cells):
                                self.cells[idx].bgcolor = self.current_color
            self.page.update()
        except RuntimeError: pass

    async def game_loop(self):
        try:
            while True:
                if self.paused or self.game_over or self.game_won:
                    await asyncio.sleep(0.1)
                    continue
                    
                new_pos = [self.current_pos[0] + 1, self.current_pos[1]]
                if not self.check_collision(new_pos, self.current_piece):
                    self.current_pos = new_pos
                else:
                    self.lock_piece()
                
                self.update_ui()
                await asyncio.sleep(0.5)
        except RuntimeError: pass

    def handle_keyboard(self, e: ft.KeyboardEvent):
        key = e.key.lower()
        if key in ["escape", "esc"]:
            if not self.game_over and not self.game_won and not self.menu_overlay.visible:
                self.paused = not self.paused
                self.pause_overlay.visible = self.paused
                self.page.update()
            return
            
        if self.game_over or self.game_won or self.paused or self.menu_overlay.visible: return
        
        if key in ["arrow left", "a", "4"]:
            new_pos = [self.current_pos[0], self.current_pos[1] - 1]
            if not self.check_collision(new_pos, self.current_piece):
                self.current_pos = new_pos
        elif key in ["arrow right", "d", "6"]:
            new_pos = [self.current_pos[0], self.current_pos[1] + 1]
            if not self.check_collision(new_pos, self.current_piece):
                self.current_pos = new_pos
        elif key in ["arrow down", "s", "2"]:
            new_pos = [self.current_pos[0] + 1, self.current_pos[1]]
            if not self.check_collision(new_pos, self.current_piece):
                self.current_pos = new_pos
        elif key in ["arrow up", "w", "8"]:
            self.rotate_piece()
        elif key == " ":
            while not self.check_collision([self.current_pos[0] + 1, self.current_pos[1]], self.current_piece):
                self.current_pos[0] += 1
            self.lock_piece()
        
        self.update_ui()

if __name__ == "__main__":
    ft.app(target=TetrisGame)
