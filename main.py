from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.core.window import Window
from kivy.uix.popup import Popup
from kivy.metrics import dp
from kivy.properties import NumericProperty, StringProperty, ListProperty, BooleanProperty
from kivy.utils import platform
from kivy.config import Config
from kivy.graphics import Color, Rectangle, Line, RoundedRectangle
from kivy.animation import Animation
from time import perf_counter
from kivy.clock import Clock
import random
import os
import json

# Настройки логирования
import logging

logging.basicConfig(level=logging.DEBUG)
Logger = logging.getLogger('CardApp')

# Глобальная настройка для имени файла с карточками
CARDS_FILENAME = 'cards.json'
# Определение константы для заголовка всплывающего окна
POPUP_TITLE_INFO = "Информация"
POPUP_TITLE_ERROR = "Ошибка"
POPUP_TITLE_SUCCESS = "Успех"

# Цветовая схема - темная тема
COLORS = {
    'background': (0.07, 0.08, 0.1, 1),
    'surface': (0.12, 0.13, 0.16, 1),
    'primary': (0.27, 0.56, 0.95, 1),
    'secondary': (0.26, 0.78, 0.54, 1),
    'text_primary': (0.96, 0.97, 0.99, 1),
    'text_secondary': (0.72, 0.76, 0.82, 1),
    'card_front': (0.18, 0.24, 0.34, 1),
    'card_back': (0.18, 0.3, 0.24, 1),
    'success': (0.25, 0.8, 0.45, 1),
    'warning': (0.98, 0.79, 0.17, 1),
    'error': (0.92, 0.28, 0.33, 1),
    'tab_active': (0.2, 0.25, 0.32, 1),
    'tab_inactive': (0.12, 0.13, 0.16, 1),
    'shadow': (0, 0, 0, 0.25)
}

# Настройки окна
Config.set('graphics', 'resizable', '1')
if platform in ('win', 'linux', 'macosx', 'unknown'):
    Window.size = (400, 600)
else:
    Window.fullscreen = 'auto'

Window.clearcolor = COLORS['background']

# Определяем путь к файлу карточек
if platform == 'android':
    try:
        from android.storage import app_storage_path  # type: ignore
        from android.permissions import request_permissions, Permission  # type: ignore

        request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])
        storage_path = app_storage_path()
        data_dir = os.path.join(storage_path, 'data')
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        CARDS_FILE = os.path.join(data_dir, CARDS_FILENAME)
    except Exception as e:
        Logger.error(f"Android init error: {e}")
        CARDS_FILE = CARDS_FILENAME
else:
    CARDS_FILE = CARDS_FILENAME


def load_cards():
    """Загружает карточки из файла"""
    try:
        if os.path.exists(CARDS_FILE) and os.path.getsize(CARDS_FILE) > 0:
            with open(CARDS_FILE, 'r', encoding='utf-8') as f:
                cards = json.load(f)
            return cards
        return []
    except Exception as ex:
        Logger.error(f"Error loading cards: {str(ex)}")
        return []


def save_cards(cards):
    """Сохраняет карточки в файл"""
    try:
        dir_name = os.path.dirname(CARDS_FILE)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name)

        with open(CARDS_FILE, 'w', encoding='utf-8') as f:
            json.dump(cards, f, ensure_ascii=False, indent=2)

        return os.path.exists(CARDS_FILE) and os.path.getsize(CARDS_FILE) > 0
    except Exception as ex:
        Logger.error(f"Error saving cards: {str(ex)}")
        return False


# Кастомная кнопка с закругленными углами
class RoundedButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0, 0, 0, 0)
        self.color = COLORS['text_primary']
        self.font_size = dp(16)
        self.border_radius = dp(15)

        with self.canvas.before:
            # Тень
            Color(*COLORS['shadow'])
            self.shadow_rect = RoundedRectangle(
                pos=self.pos,
                size=(self.size[0], self.size[1]),
                radius=[self.border_radius]
            )
            # Фон
            Color(*COLORS['primary'])
            self.rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[self.border_radius]
            )

        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
        self.shadow_rect.pos = (self.pos[0], self.pos[1] - dp(2))
        self.shadow_rect.size = (self.size[0], self.size[1])


# Кастомное текстовое поле с закругленными углами
class RoundedTextInput(TextInput):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0, 0, 0, 0)
        self.background_normal = ''
        self.background_active = ''
        self.background_disabled_normal = ''
        self.background_disabled_active = ''
        self.foreground_color = COLORS['text_primary']  # Цвет текста
        self.disabled_foreground_color = COLORS['text_secondary']
        self.cursor_color = (1, 1, 1, 1)
        self.cursor_blink = False
        self.cursor_width = dp(3)
        self.selection_color = (
            COLORS['primary'][0], COLORS['primary'][1], COLORS['primary'][2], 0.35
        )
        self.border_radius = dp(10)
        self.padding = [dp(15), dp(10), dp(15), dp(10)]
        self.hint_text_color = COLORS['text_secondary']
        self.write_tab = False  # Отключаем табуляцию
        self._saved_hint_text = self.hint_text

        with self.canvas.before:
            Color(*COLORS['surface'])
            self.bg_rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[self.border_radius]
            )
            Color(*COLORS['primary'])
            self.border_line = Line(
                rounded_rectangle=(self.pos[0], self.pos[1], self.size[0], self.size[1], self.border_radius),
                width=1.5
            )
        # Выше канваса (после canvas.before) курсор и текст рисуются корректно

        self.bind(pos=self.update_rect, size=self.update_rect)
        self.bind(focus=self._on_focus_change)

        # Пользовательский курсор поверх (на случай, если системный не виден)
        with self.canvas.after:
            self._caret_color = Color(1, 1, 1, 1)
            self._caret = Rectangle(pos=self.pos, size=(dp(2), self.line_height))
        self.bind(cursor_pos=self._update_caret, focus=self._update_caret, size=self._update_caret, text=self._update_caret)
        self._caret_visible = True
        self._blink_event = None

    def update_rect(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        self.border_line.rounded_rectangle = (
            self.pos[0], self.pos[1], self.size[0], self.size[1], self.border_radius
        )

    def _on_focus_change(self, _instance, value):
        if value:
            # На фокусе скрываем hint, чтобы был виден курсор
            if self.text == '':
                self._saved_hint_text = self.hint_text
                self.hint_text = ''
            # Запускаем мигание
            self._start_caret_blink()
        else:
            # Без фокуса возвращаем hint, если поле пустое
            if self.text == '' and self._saved_hint_text is not None:
                self.hint_text = self._saved_hint_text
            # Останавливаем мигание и прячем курсор
            self._stop_caret_blink()
        # Обновляем курсор при смене фокуса
        self._update_caret()

    def _update_caret(self, *args):
        try:
            if not hasattr(self, '_caret'):
                return
            if not self.focus:
                # Скрываем кастомный курсор, если нет фокуса
                self._caret.size = (0, 0)
                return
            cx, cy = self.cursor_pos
            caret_width = dp(2)
            caret_height = max(dp(14), self.line_height)
            # Ограничиваем в границах виджета
            cx = max(self.x + dp(2), min(cx, self.right - dp(2)))
            cy = max(self.y + dp(2), min(cy, self.top - dp(2)))
            self._caret.pos = (cx, cy - caret_height * 0.75)
            self._caret.size = (caret_width, caret_height)
            # При любом обновлении делаем курсор видимым и сбрасываем альфу
            if hasattr(self, '_caret_color'):
                self._caret_color.a = 1
                self._caret_visible = True
        except Exception:
            pass

    def _start_caret_blink(self):
        try:
            if self._blink_event is not None:
                self._blink_event.cancel()
            # Мигание каждые 0.5с
            self._blink_event = Clock.schedule_interval(self._blink_tick, 0.5)
        except Exception:
            self._blink_event = None

    def _stop_caret_blink(self):
        try:
            if self._blink_event is not None:
                self._blink_event.cancel()
                self._blink_event = None
            # Скрываем курсор при потере фокуса
            if hasattr(self, '_caret_color'):
                self._caret_color.a = 0
        except Exception:
            pass

    def _blink_tick(self, dt):
        try:
            if not self.focus or not hasattr(self, '_caret_color'):
                return
            self._caret_visible = not self._caret_visible
            self._caret_color.a = 1 if self._caret_visible else 0
        except Exception:
            pass


# Кастомное текстовое поле с автоматическим изменением высоты
class AutoHeightTextInput(RoundedTextInput):
    min_height = NumericProperty(dp(40))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(text=self.on_text_change)
        self.height = self.min_height
        # Убедимся, что текст виден
        self.foreground_color = COLORS['text_primary']
        self.hint_text_color = COLORS['text_secondary']
        self.cursor_color = (1, 1, 1, 1)
        self.cursor_blink = False
        self.cursor_width = dp(3)
        self.background_color = (0, 0, 0, 0)
        self.background_normal = ''
        self.background_active = ''
        # Отрисовка кастомного курсора уже унаследована из RoundedTextInput

    def on_text_change(self, _instance, _value):
        lines = len(self._lines)
        line_height = self.line_height + self.line_spacing
        new_height = max(self.min_height, lines * line_height + self.padding[1] + self.padding[3])
        if new_height != self.height:
            self.height = new_height


# Кастомная вкладка с изменением цвета при активации
class CustomTabbedPanelItem(TabbedPanelItem):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = COLORS['tab_inactive']
        self.color = COLORS['text_primary']
        with self.canvas.before:
            Color(*COLORS['shadow'])
            self.shadow = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])
            Color(*self.background_color)
            self.bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])
        self.bind(state=self._update_color)
        self.bind(pos=self._repaint, size=self._repaint)

    def _update_color(self, instance, value):
        if self.state == 'down':
            self.background_color = COLORS['tab_active']
        else:
            self.background_color = COLORS['tab_inactive']
        self._repaint()

    def _repaint(self, *args):
        if hasattr(self, 'shadow') and hasattr(self, 'bg'):
            self.shadow.pos = (self.pos[0], self.pos[1] - dp(1))
            self.shadow.size = self.size
            self.bg.pos = self.pos
            self.bg.size = self.size


# Улучшенный виджет карточки для обучения с адаптивным размером
class LearningCard(BoxLayout):
    front_text = StringProperty('')
    back_text = StringProperty('')
    current_side = StringProperty('front')

    def __init__(self, front_text, back_text, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (0.95, 1)
        self.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        self.padding = dp(20)
        self.spacing = dp(10)

        self.front_text = front_text
        self.back_text = back_text
        self.current_side = 'front'
        self.border_radius = dp(20)
        self._tap_start_pos = None
        self._start_scroll_y = None
        self._did_scroll_move = False
        self._tap_time_start = 0.0

        # Создаем фон карточки
        with self.canvas.before:
            # Тень
            Color(*COLORS['shadow'])
            self.shadow = RoundedRectangle(
                pos=(self.pos[0], self.pos[1] - dp(3)),
                size=self.size,
                radius=[self.border_radius]
            )
            # Карточка
            Color(*COLORS['card_front'])
            self.rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[self.border_radius]
            )
            Color(*COLORS['primary'])
            self.border = Line(
                rounded_rectangle=(self.pos[0], self.pos[1], self.size[0], self.size[1], self.border_radius),
                width=1.5
            )

        # Прокручиваемый текст карточки
        self.scroll_view = ScrollView(
            size_hint=(1, 1),
            bar_width=0,
            do_scroll_x=False,
            bar_color=(0, 0, 0, 0),
            bar_inactive_color=(0, 0, 0, 0),
            scroll_type=['content']
        )
        self.card_label = Label(
            text=self.front_text,
            size_hint_y=None,
            text_size=(Window.width * 0.8 - dp(40), None),
            halign='center',
            valign='middle',
            font_size=dp(18),
            color=COLORS['text_primary'],
            bold=True
        )
        self.card_label.bind(texture_size=self._update_label_height)
        self.scroll_view.add_widget(self.card_label)
        self.add_widget(self.scroll_view)

        self.bind(pos=self.update_graphics, size=self.update_graphics)
        self.bind(size=self._update_label_width)
        Clock.schedule_once(lambda dt: self._update_label_width(self, None), 0)

        # На стороне вопроса (front) отключаем вертикальный скролл
        self.scroll_view.do_scroll_y = False

    def _update_label_height(self, instance, value):
        instance.height = max(dp(100), value[1])

    def _update_label_width(self, _instance, _value):
        padding_total = dp(40)
        new_width = max(0, self.width - padding_total)
        if self.card_label.text_size[0] != new_width:
            self.card_label.text_size = (new_width, None)

    def update_graphics(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
        self.border.rounded_rectangle = (self.pos[0], self.pos[1], self.size[0], self.size[1], self.border_radius)
        if hasattr(self, 'shadow'):
            self.shadow.pos = (self.pos[0], self.pos[1] - dp(3))
            self.shadow.size = self.size

    def flip_card(self):
        if self.current_side == 'front':
            self.current_side = 'back'
            self.card_label.text = self.back_text
            # Изменяем стиль для обратной стороны
            self.card_label.halign = 'left'
            self.card_label.bold = False
            self.card_label.font_size = dp(16)
            # На стороне ответа включаем вертикальный скролл
            self.scroll_view.do_scroll_y = True

            self.canvas.before.clear()
            with self.canvas.before:
                Color(*COLORS['shadow'])
                self.shadow = RoundedRectangle(
                    pos=(self.pos[0], self.pos[1] - dp(3)),
                    size=self.size,
                    radius=[self.border_radius]
                )
                Color(*COLORS['card_back'])
                self.rect = RoundedRectangle(
                    pos=self.pos,
                    size=self.size,
                    radius=[self.border_radius]
                )
                Color(*COLORS['secondary'])
                self.border = Line(
                    rounded_rectangle=(self.pos[0], self.pos[1], self.size[0], self.size[1], self.border_radius),
                    width=1.5
                )
        else:
            self.current_side = 'front'
            self.card_label.text = self.front_text
            # Возвращаем стиль для передней стороны
            self.card_label.halign = 'center'
            self.card_label.bold = True
            self.card_label.font_size = dp(18)
            # На стороне вопроса отключаем вертикальный скролл
            self.scroll_view.do_scroll_y = False

            self.canvas.before.clear()
            with self.canvas.before:
                Color(*COLORS['shadow'])
                self.shadow = RoundedRectangle(
                    pos=(self.pos[0], self.pos[1] - dp(3)),
                    size=self.size,
                    radius=[self.border_radius]
                )
                Color(*COLORS['card_front'])
                self.rect = RoundedRectangle(
                    pos=self.pos,
                    size=self.size,
                    radius=[self.border_radius]
                )
                Color(*COLORS['primary'])
                self.border = Line(
                    rounded_rectangle=(self.pos[0], self.pos[1], self.size[0], self.size[1], self.border_radius),
                    width=1.5
                )

        anim = Animation(opacity=0, duration=0.1) + Animation(opacity=1, duration=0.1)
        anim.start(self.card_label)
        anim.start(self.card_label)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            in_scroll = self.scroll_view.collide_point(*touch.pos)
            is_scrollable = self.card_label.height > self.scroll_view.height
            # На стороне ответа: если тап начался внутри области скролла и контент скроллится,
            # не считаем это началом «тапа для переворота»
            if self.current_side == 'back' and is_scrollable and in_scroll:
                return super().on_touch_down(touch)
            self._tap_start_pos = touch.pos
            self._start_scroll_y = self.scroll_view.scroll_y
            self._did_scroll_move = False
            self._tap_time_start = perf_counter()
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self._tap_start_pos and self.collide_point(*touch.pos):
            dx = abs(touch.pos[0] - self._tap_start_pos[0])
            dy = abs(touch.pos[1] - self._tap_start_pos[1])
            sc_delta = 0 if self._start_scroll_y is None else abs(self.scroll_view.scroll_y - self._start_scroll_y)
            # Учитываем оверскролл по эффекту
            effect_dist = 0
            try:
                if hasattr(self.scroll_view, 'effect_y') and self.scroll_view.effect_y is not None:
                    effect_dist = abs(getattr(self.scroll_view.effect_y, 'distance', 0))
            except Exception:
                effect_dist = 0

            if dy > dp(1) or sc_delta > 0.0005 or effect_dist > 0:
                self._did_scroll_move = True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        handled = super().on_touch_up(touch)
        # Если «тап для переворота» не был начат, выходим
        if self._tap_start_pos is None:
            return handled
        if self._tap_start_pos and self.collide_point(*touch.pos):
            dx = abs(touch.pos[0] - self._tap_start_pos[0])
            dy = abs(touch.pos[1] - self._tap_start_pos[1])
            sc_delta = 0 if self._start_scroll_y is None else abs(self.scroll_view.scroll_y - self._start_scroll_y)
            # Если есть прокручиваемый контент и была вертикальная протяжка — блокируем переворот
            is_scrollable = self.card_label.height > self.scroll_view.height
            if is_scrollable and dy > dp(1):
                self._did_scroll_move = True

            tap_duration = perf_counter() - (self._tap_time_start or perf_counter())
            in_scroll = self.scroll_view.collide_point(*touch.pos)
            # Учитываем оверскролл по эффекту
            effect_dist = 0
            try:
                if hasattr(self.scroll_view, 'effect_y') and self.scroll_view.effect_y is not None:
                    effect_dist = abs(getattr(self.scroll_view.effect_y, 'distance', 0))
            except Exception:
                effect_dist = 0

            # На стороне ответа: внутри ScrollView не переворачиваем, если был скролл/движение;
            # На стороне вопроса: переворот по тапу везде (скролл отключен)
            if self.current_side == 'back' and is_scrollable and in_scroll:
                flip_allowed = (
                    not self._did_scroll_move
                    and dx < dp(5)
                    and dy < dp(3)
                    and sc_delta < 0.005
                    and effect_dist == 0
                    and tap_duration < 0.15
                )
            else:
                flip_allowed = (
                    not self._did_scroll_move
                    and dx < dp(5)
                    and dy < dp(3)
                    and sc_delta < 0.005
                    and tap_duration < 0.15
                )

            if flip_allowed:
                self.flip_card()
                self._tap_start_pos = None
                self._start_scroll_y = None
                self._did_scroll_move = False
                return True
        self._tap_start_pos = None
        self._start_scroll_y = None
        self._did_scroll_move = False
        return handled


class CardApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tabs = None
        self.add_content = None
        self.learn_content = None
        self.edit_content = None

    def build(self):
        self.tabs = TabbedPanel(do_default_tab=False)
        self.tabs.background_color = COLORS['surface']
        self.tabs.border = [0, 0, 0, 0]
        self.tabs.tab_width = dp(100)

        # Вкладка создания карточек
        add_tab = CustomTabbedPanelItem(text='Создать')
        self.add_content = AddCardTab(app=self)
        add_tab.add_widget(self.add_content)
        self.tabs.add_widget(add_tab)

        # Вкладка обучения
        learn_tab = CustomTabbedPanelItem(text='Учить')
        self.learn_content = LearningTab(app=self)
        learn_tab.add_widget(self.learn_content)
        self.tabs.add_widget(learn_tab)

        # Вкладка редактирования
        edit_tab = CustomTabbedPanelItem(text='Список')
        self.edit_content = EditCardsTab(app=self)
        edit_tab.add_widget(self.edit_content)
        self.tabs.add_widget(edit_tab)

        return self.tabs

    def update_cards(self):
        if hasattr(self, 'learn_content'):
            self.learn_content.reset_session()
        if hasattr(self, 'edit_content'):
            self.edit_content.load_cards()
        if hasattr(self, 'add_content'):
            self.add_content.front_input.text = ''
            self.add_content.back_input.text = ''

    @staticmethod
    def show_popup(title, message):
        popup_layout = BoxLayout(orientation='vertical', padding=dp(10))
        popup_layout.canvas.before.clear()
        with popup_layout.canvas.before:
            Color(*COLORS['surface'])
            Rectangle(pos=popup_layout.pos, size=popup_layout.size)

        message_label = Label(
            text=message,
            font_size=dp(16),
            color=COLORS['text_primary'],
            text_size=(Window.width * 0.7, None)
        )
        popup_layout.add_widget(message_label)

        close_btn = RoundedButton(text='OK', size_hint_y=None, height=dp(40))
        popup = Popup(
            title=title,
            content=popup_layout,
            size_hint=(0.8, 0.4),
            background='',
            separator_color=COLORS['primary']
        )
        popup.title_color = COLORS['text_primary']
        popup.background_color = COLORS['surface']

        close_btn.bind(on_press=popup.dismiss)
        popup_layout.add_widget(close_btn)
        popup.open()


class AddCardTab(BoxLayout):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.orientation = 'vertical'
        self.padding = dp(15)
        self.spacing = dp(15)

        title_label = Label(
            text='Создание карточки',
            size_hint_y=None,
            height=dp(40),
            font_size=dp(22),
            bold=True,
            color=COLORS['text_primary']
        )
        self.add_widget(title_label)

        # Поле лицевой стороны карточки
        front_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(150))
        front_label = Label(
            text='Передняя сторона (вопрос):',
            size_hint_y=None,
            height=dp(30),
            font_size=dp(16),
            color=COLORS['text_primary']
        )
        front_layout.add_widget(front_label)
        self.front_input = AutoHeightTextInput(
            multiline=True,
            size_hint_y=1,
            min_height=dp(120),
            font_size=dp(14),
            hint_text='Введите вопрос или термин'
        )
        front_layout.add_widget(self.front_input)
        self.add_widget(front_layout)

        # Поле обратной стороны карточки
        back_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(150))
        back_label = Label(
            text='Обратная сторона (ответ):',
            size_hint_y=None,
            height=dp(30),
            font_size=dp(16),
            color=COLORS['text_primary']
        )
        back_layout.add_widget(back_label)
        self.back_input = AutoHeightTextInput(
            multiline=True,
            size_hint_y=1,
            min_height=dp(120),
            font_size=dp(14),
            hint_text='Введите ответ или определение'
        )
        back_layout.add_widget(self.back_input)
        self.add_widget(back_layout)

        self.save_btn = RoundedButton(text='Создать карточку', size_hint_y=None, height=dp(50))
        self.save_btn.bind(on_press=self.save_card)
        self.add_widget(self.save_btn)

    def save_card(self, _instance):
        front_text = self.front_input.text.strip()
        back_text = self.back_input.text.strip()

        if not front_text:
            self.show_popup(POPUP_TITLE_ERROR, "Введите текст передней стороны!")
            return

        if not back_text:
            self.show_popup(POPUP_TITLE_ERROR, "Введите текст обратной стороны!")
            return

        cards = load_cards()
        card_data = {'front': front_text, 'back': back_text}
        cards.append(card_data)

        if not save_cards(cards):
            self.show_popup(POPUP_TITLE_ERROR, "Не удалось сохранить карточку!")
            return

        self.front_input.text = ''
        self.back_input.text = ''
        self.app.update_cards()
        self.show_popup(POPUP_TITLE_SUCCESS, "Карточка создана!")

    @staticmethod
    def show_popup(title, message):
        CardApp.show_popup(title, message)


class LearningTab(BoxLayout):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.orientation = 'vertical'
        self.padding = dp(15)
        self.spacing = dp(15)

        self.current_card_index = 0
        self.cards_to_review = []
        self.all_cards = []
        self.learned_cards = set()
        self.current_card_widget = None

        self._setup_ui()
        self.reset_session()

    def _setup_ui(self):
        title_label = Label(
            text='Обучение по карточкам',
            size_hint_y=None,
            height=dp(40),
            font_size=dp(22),
            bold=True,
            color=COLORS['text_primary']
        )
        self.add_widget(title_label)

        self.counter_label = Label(
            text='',
            size_hint_y=None,
            height=dp(30),
            font_size=dp(16),
            color=COLORS['text_primary']
        )
        self.add_widget(self.counter_label)

        from kivy.uix.floatlayout import FloatLayout
        self.card_area = FloatLayout(size_hint=(1, 0.7))
        self.add_widget(self.card_area)

        self._create_control_buttons()

        instruction_label = Label(
            text='Нажмите на карточку чтобы перевернуть\nКнопки ниже для управления',
            size_hint_y=None,
            height=dp(60),
            font_size=dp(14),
            text_size=(Window.width - dp(20), None),
            halign='center',
            color=COLORS['text_secondary']
        )
        self.add_widget(instruction_label)

    def _create_control_buttons(self):
        btn_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))

        # Кнопка "Повторить" - желтая
        self.repeat_btn = Button(
            text='Повторить',
            background_color=COLORS['warning'],
            color=COLORS['text_primary']
        )
        self.repeat_btn.bind(on_press=lambda x: self.on_swipe_left())

        # Кнопка переворота - синяя
        self.flip_btn = Button(
            text='Перевернуть',
            background_color=COLORS['primary'],
            color=COLORS['text_primary']
        )
        self.flip_btn.bind(on_press=lambda x: self.flip_current_card())

        # Кнопка "Знаю" - зеленая
        self.know_btn = Button(
            text='Знаю',
            background_color=COLORS['success'],
            color=COLORS['text_primary']
        )
        self.know_btn.bind(on_press=lambda x: self.on_swipe_right())

        btn_layout.add_widget(self.repeat_btn)
        btn_layout.add_widget(self.flip_btn)
        btn_layout.add_widget(self.know_btn)
        self.add_widget(btn_layout)

        reset_btn = Button(
            text='Начать заново',
            size_hint_y=None,
            height=dp(40),
            background_color=COLORS['surface'],
            color=COLORS['text_primary']
        )
        reset_btn.bind(on_press=self.reset_session)
        self.add_widget(reset_btn)

    def reset_session(self, _instance=None):
        all_cards = load_cards()
        if not all_cards:
            self.show_no_cards_message()
            return

        self.all_cards = all_cards.copy()
        random.shuffle(self.all_cards)
        self.cards_to_review = []
        self.current_card_index = 0
        self.learned_cards = set()

        self.update_counter()
        self.show_next_card()

    def show_no_cards_message(self):
        self.card_area.clear_widgets()
        no_cards_label = Label(
            text='Нет карточек для обучения!\nСоздайте карточки на вкладке "Создать карточку"',
            font_size=dp(18),
            text_size=(Window.width - dp(40), None),
            halign='center',
            valign='middle',
            size_hint=(0.9, 0.6),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            color=COLORS['text_primary']
        )
        self.card_area.add_widget(no_cards_label)
        self.counter_label.text = 'Нет карточек'

    def update_counter(self):
        total_cards = len(self.all_cards)
        cards_in_review = len(self.cards_to_review)
        learned_count = len(self.learned_cards)

        if self.current_card_index < len(self.all_cards):
            self.counter_label.text = f'Карточка: {self.current_card_index + 1}/{total_cards} | Выучено: {learned_count}'
        else:
            self.counter_label.text = f'Повторение: {cards_in_review} карточек | Выучено: {learned_count}'

    def show_next_card(self):
        self.card_area.clear_widgets()

        if self.current_card_index < len(self.all_cards):
            card = self.all_cards[self.current_card_index]
            self._display_card(card)
            return

        if self.cards_to_review:
            random.shuffle(self.cards_to_review)
            self.all_cards = self.cards_to_review.copy()
            self.cards_to_review = []
            self.current_card_index = 0

            card = self.all_cards[self.current_card_index]
            self._display_card(card)
            return

        self.show_session_complete()

    def _display_card(self, card):
        card_widget = LearningCard(front_text=card['front'], back_text=card['back'])
        self.current_card_widget = card_widget
        self.card_area.add_widget(card_widget)
        self.update_counter()

    # Переворот теперь обрабатывается внутри LearningCard, чтобы не мешать скроллу

    def flip_current_card(self):
        if self.current_card_widget:
            self.current_card_widget.flip_card()

    def on_swipe_right(self):
        if self.current_card_index < len(self.all_cards):
            current_card = self.all_cards[self.current_card_index]
            card_id = f"{current_card['front']}_{current_card['back']}"
            self.learned_cards.add(card_id)

        self.current_card_index += 1
        self.show_next_card()

    def on_swipe_left(self):
        if self.current_card_index < len(self.all_cards):
            card = self.all_cards[self.current_card_index]
            self.cards_to_review.append(card)

        self.current_card_index += 1
        self.show_next_card()

    def show_session_complete(self):
        self.card_area.clear_widgets()
        complete_label = Label(
            text='Сессия завершена!\n\nВсе карточки изучены.',
            font_size=dp(20),
            text_size=(Window.width - dp(40), None),
            halign='center',
            valign='middle',
            size_hint=(0.9, 0.6),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            color=COLORS['text_primary']
        )
        self.card_area.add_widget(complete_label)
        self.counter_label.text = 'Сессия завершена'


class EditCardsTab(BoxLayout):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.current_edit_index = None
        self._setup_ui()
        self.load_cards()

    def _setup_ui(self):
        self.orientation = 'vertical'
        self.padding = dp(15)
        self.spacing = dp(15)

        self._create_title()
        self._create_cards_list()
        self._create_control_buttons()

    def _create_title(self):
        title_label = Label(
            text='Список карточек',
            size_hint_y=None,
            height=dp(40),
            font_size=dp(22),
            bold=True,
            color=COLORS['text_primary']
        )
        self.add_widget(title_label)

    def _create_cards_list(self):
        self.cards_scroll = ScrollView(
            size_hint=(1, 0.6),
            bar_width=0,
            do_scroll_x=False,
            bar_color=(0, 0, 0, 0),
            bar_inactive_color=(0, 0, 0, 0),
            scroll_type=['content']
        )

        # Добавляем фон для ScrollView
        with self.cards_scroll.canvas.before:
            Color(*COLORS['background'])
            self.scroll_bg = Rectangle(pos=self.cards_scroll.pos, size=self.cards_scroll.size)

        self.cards_scroll.bind(pos=self._update_scroll_bg, size=self._update_scroll_bg)

        self.cards_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(5))
        self.cards_layout.bind(minimum_height=self.cards_layout.setter('height'))
        self.cards_scroll.add_widget(self.cards_layout)
        self.add_widget(self.cards_scroll)

    def _update_scroll_bg(self, *args):
        if hasattr(self, 'scroll_bg'):
            self.scroll_bg.pos = self.cards_scroll.pos
            self.scroll_bg.size = self.cards_scroll.size

    def _create_control_buttons(self):
        self._create_refresh_button()
        self._create_export_import_buttons()
        self._create_session_buttons()

    def _create_refresh_button(self):
        self.refresh_btn = Button(
            text='Обновить список',
            size_hint_y=None,
            height=dp(40),
            background_color=COLORS['primary'],
            color=COLORS['text_primary']
        )
        self.refresh_btn.bind(on_press=self.load_cards)
        self.add_widget(self.refresh_btn)

    def _create_export_import_buttons(self):
        export_import_layout = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(5))

        self.export_btn = Button(
            text='Экспорт',
            size_hint_x=0.5,
            background_color=COLORS['primary'],
            color=COLORS['text_primary']
        )
        self.export_btn.bind(on_press=self.export_database)
        export_import_layout.add_widget(self.export_btn)

        self.import_btn = Button(
            text='Импорт',
            size_hint_x=0.5,
            background_color=COLORS['primary'],
            color=COLORS['text_primary']
        )
        self.import_btn.bind(on_press=self.import_database)
        export_import_layout.add_widget(self.import_btn)

        self.add_widget(export_import_layout)

    def _create_session_buttons(self):
        self.reset_session_btn = Button(
            text='Сбросить сессию обучения',
            size_hint_y=None,
            height=dp(40),
            background_color=COLORS['surface'],
            color=COLORS['text_primary']
        )
        self.reset_session_btn.bind(on_press=self.reset_learning_session)
        self.add_widget(self.reset_session_btn)

        self.check_db_btn = Button(
            text='Проверить состояние базы',
            size_hint_y=None,
            height=dp(40),
            background_color=COLORS['surface'],
            color=COLORS['text_primary']
        )
        self.check_db_btn.bind(on_press=self.check_database_status)
        self.add_widget(self.check_db_btn)

    def load_cards(self, _instance=None):
        self.cards_layout.clear_widgets()
        cards = load_cards()

        if not cards:
            self._show_no_cards_message()
            return

        self._display_cards_list(cards)

    def _show_no_cards_message(self):
        no_cards_label = Label(
            text='В базе нет карточек.',
            size_hint_y=None,
            height=dp(40),
            font_size=dp(16),
            color=COLORS['text_primary']
        )
        self.cards_layout.add_widget(no_cards_label)

    def _display_cards_list(self, cards):
        for idx, card in enumerate(cards):
            self._create_card_item(idx, card)

    def _create_card_item(self, index, card):
        card_item = BoxLayout(size_hint_y=None, height=dp(80), spacing=dp(5), padding=dp(5))

        with card_item.canvas.before:
            Color(*COLORS['surface'])
            card_item.bg_rect = RoundedRectangle(pos=card_item.pos, size=card_item.size, radius=[dp(10)])

        def _update_bg_rect(_instance, _value):
            if hasattr(card_item, 'bg_rect'):
                card_item.bg_rect.pos = card_item.pos
                card_item.bg_rect.size = card_item.size

        card_item.bind(pos=_update_bg_rect, size=_update_bg_rect)

        card_text = self._format_card_text(card)
        card_label = Label(
            text=card_text,
            size_hint_x=0.7,
            text_size=(Window.width * 0.7 - dp(20), None),
            halign='left',
            valign='middle',
            color=COLORS['text_primary']
        )
        card_label.bind(size=card_label.setter('text_size'))

        btn_layout = self._create_card_buttons(index, card)

        card_item.add_widget(card_label)
        card_item.add_widget(btn_layout)
        self.cards_layout.add_widget(card_item)

    @staticmethod
    def _format_card_text(card):
        front_short = card['front'][:25] + '...' if len(card['front']) > 25 else card['front']
        back_short = card['back'][:25] + '...' if len(card['back']) > 25 else card['back']
        return f"В: {front_short}\nО: {back_short}"

    def _create_card_buttons(self, index, _card):
        btn_layout = BoxLayout(size_hint_x=0.3, spacing=dp(2))

        edit_btn = Button(
            text='Изменить',
            size_hint_x=0.5,
            font_size=dp(10),
            background_color=COLORS['primary'],
            color=COLORS['text_primary']
        )
        edit_btn.bind(on_press=lambda inst: self.edit_card(index, load_cards()))

        delete_btn = Button(
            text='Удалить',
            size_hint_x=0.5,
            font_size=dp(10),
            background_color=COLORS['error'],
            color=COLORS['text_primary']
        )
        delete_btn.bind(on_press=lambda inst: self.delete_card(index, load_cards()))

        btn_layout.add_widget(edit_btn)
        btn_layout.add_widget(delete_btn)

        return btn_layout

    def edit_card(self, index, cards):
        self.current_edit_index = index
        card_data = cards[index]

        popup_layout = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(15))
        popup_layout.canvas.before.clear()
        with popup_layout.canvas.before:
            Color(*COLORS['surface'])
            Rectangle(pos=popup_layout.pos, size=popup_layout.size)

        popup = Popup(
            title='Редактирование карточки',
            content=popup_layout,
            size_hint=(0.95, 0.8),
            background='',
            separator_color=COLORS['primary']
        )
        popup.title_color = COLORS['text_primary']
        popup.background_color = COLORS['surface']

        front_label = Label(text='Передняя сторона:', size_hint_y=None, height=dp(30), color=COLORS['text_primary'])
        popup_layout.add_widget(front_label)
        front_input = AutoHeightTextInput(
            text=card_data['front'],
            multiline=True,
            size_hint_y=None,
            min_height=dp(100),
            font_size=dp(14)
        )
        popup_layout.add_widget(front_input)

        back_label = Label(text='Обратная сторона:', size_hint_y=None, height=dp(30), color=COLORS['text_primary'])
        popup_layout.add_widget(back_label)
        back_input = AutoHeightTextInput(
            text=card_data['back'],
            multiline=True,
            size_hint_y=None,
            min_height=dp(100),
            font_size=dp(14)
        )
        popup_layout.add_widget(back_input)

        btn_layout = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(5))
        save_btn = Button(text='Сохранить', background_color=COLORS['primary'], color=COLORS['text_primary'])
        cancel_btn = Button(text='Отмена', background_color=COLORS['surface'], color=COLORS['text_primary'])

        def save_card(_instance):
            front_text = front_input.text.strip()
            back_text = back_input.text.strip()

            if not front_text or not back_text:
                self.show_popup(POPUP_TITLE_ERROR, "Обе стороны карточки должны быть заполнены!")
                return

            cards[self.current_edit_index] = {'front': front_text, 'back': back_text}

            if save_cards(cards):
                popup.dismiss()
                self.load_cards()
                self.app.update_cards()
                self.show_popup(POPUP_TITLE_SUCCESS, "Карточка обновлена!")
            else:
                self.show_popup(POPUP_TITLE_ERROR, "Не удалось сохранить карточки!")

        save_btn.bind(on_press=save_card)
        cancel_btn.bind(on_press=popup.dismiss)

        btn_layout.add_widget(save_btn)
        btn_layout.add_widget(cancel_btn)
        popup_layout.add_widget(btn_layout)

        popup.open()

    def delete_card(self, index, cards):
        if 0 <= index < len(cards):
            self._show_delete_confirmation(index, cards)

    def _show_delete_confirmation(self, index, cards):
        confirm_layout = BoxLayout(orientation='vertical', padding=dp(10))
        confirm_layout.canvas.before.clear()
        with confirm_layout.canvas.before:
            Color(*COLORS['surface'])
            Rectangle(pos=confirm_layout.pos, size=confirm_layout.size)

        confirm_label = Label(
            text=f'Вы уверены, что хотите удалить карточку?\n\n{cards[index]["front"][:50]}...',
            text_size=(Window.width * 0.8 - dp(20), None),
            color=COLORS['text_primary']
        )
        confirm_layout.add_widget(confirm_label)

        btn_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        yes_btn = Button(text='Да', background_color=COLORS['error'], color=COLORS['text_primary'])
        no_btn = Button(text='Нет', background_color=COLORS['surface'], color=COLORS['text_primary'])

        confirm_popup = Popup(
            title='Подтверждение удаления',
            content=confirm_layout,
            size_hint=(0.8, 0.4),
            background='',
            separator_color=COLORS['primary']
        )
        confirm_popup.title_color = COLORS['text_primary']
        confirm_popup.background_color = COLORS['surface']

        yes_btn.bind(on_press=lambda x: self._confirm_delete(index, cards, confirm_popup))
        no_btn.bind(on_press=confirm_popup.dismiss)

        btn_layout.add_widget(yes_btn)
        btn_layout.add_widget(no_btn)
        confirm_layout.add_widget(btn_layout)

        confirm_popup.open()

    def _confirm_delete(self, index, cards, popup):
        cards.pop(index)
        if save_cards(cards):
            popup.dismiss()
            self.load_cards()
            self.app.update_cards()
            self.show_popup(POPUP_TITLE_SUCCESS, "Карточка удалена!")
        else:
            self.show_popup(POPUP_TITLE_ERROR, "Не удалось сохранить карточки!")

    def reset_learning_session(self, _instance):
        if hasattr(self.app, 'learn_content'):
            self.app.learn_content.reset_session()
            self.show_popup(POPUP_TITLE_SUCCESS, "Сессия обучения сброшена!")

    def check_database_status(self, _instance):
        cards = load_cards()
        db_path = CARDS_FILE
        db_exists = os.path.exists(db_path)
        db_size = os.path.getsize(db_path) if db_exists else 0

        message = f"""Путь к базе: {db_path}
Файл существует: {'Да' if db_exists else 'Нет'}
Размер файла: {db_size} байт
Количество карточек: {len(cards)}"""

        self.show_popup("Состояние базы данных", message)

    def export_database(self, _instance):
        try:
            cards = load_cards()
            if not cards:
                self.show_popup(POPUP_TITLE_ERROR, "Нет карточек для экспорта")
                return

            if platform == 'android':
                self._export_android(cards)
            else:
                self._export_desktop(cards)
        except Exception as ex:
            self.show_popup(POPUP_TITLE_ERROR, f"Ошибка экспорта: {str(ex)}")

    def import_database(self, _instance):
        try:
            if platform == 'android':
                self._import_android()
            else:
                self._import_desktop()
        except Exception as ex:
            self.show_popup(POPUP_TITLE_ERROR, f"Ошибка импорта: {str(ex)}")

    def _export_android(self, cards):
        from android.storage import primary_external_storage_path  # type: ignore
        downloads_path = os.path.join(primary_external_storage_path(), "Download")
        export_path = os.path.join(downloads_path, "cards_export.json")

        if not os.path.exists(downloads_path):
            os.makedirs(downloads_path)

        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump(cards, f, ensure_ascii=False, indent=2)

        self.show_popup(POPUP_TITLE_SUCCESS, f"База экспортирована в:\n{export_path}")

    def _export_desktop(self, cards):
        home_dir = os.path.expanduser("~")
        downloads_path = os.path.join(home_dir, 'Downloads')

        if not os.path.exists(downloads_path):
            os.makedirs(downloads_path)

        export_path = os.path.join(downloads_path, 'cards_export.json')
        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump(cards, f, ensure_ascii=False, indent=2)

        self.show_popup(POPUP_TITLE_SUCCESS, f"База экспортирована в:\n{export_path}")

    def _import_android(self):
        from android.storage import primary_external_storage_path  # type: ignore
        downloads_path = os.path.join(primary_external_storage_path(), "Download")
        import_path = os.path.join(downloads_path, "cards_export.json")

        if not os.path.exists(import_path):
            self.show_popup(POPUP_TITLE_ERROR, "Файл cards_export.json не найден")
            return

        self._import_cards_from_file(import_path)

    def _import_desktop(self):
        from tkinter import Tk, filedialog
        root = Tk()
        root.withdraw()
        root.attributes('-topmost', True)

        downloads_path = os.path.join(os.path.expanduser("~"), 'Downloads')
        file_path = filedialog.askopenfilename(
            initialdir=downloads_path,
            title="Выберите файл с карточками",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        root.destroy()

        if not file_path:
            return

        self._import_cards_from_file(file_path)

    def _import_cards_from_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            imported_cards = json.load(f)

        if not self._validate_imported_cards(imported_cards):
            return

        if save_cards(imported_cards):
            self.show_popup(POPUP_TITLE_SUCCESS, f"Импортировано {len(imported_cards)} карточек")
            self.app.update_cards()
            self.load_cards()
        else:
            self.show_popup(POPUP_TITLE_ERROR, "Ошибка сохранения импортированной базы")

    def _validate_imported_cards(self, imported_cards):
        if not isinstance(imported_cards, list):
            self.show_popup(POPUP_TITLE_ERROR, "Некорректный формат файла")
            return False

        valid_cards = [c for c in imported_cards if isinstance(c, dict) and 'front' in c and 'back' in c]
        if not valid_cards:
            self.show_popup(POPUP_TITLE_ERROR, "Нет валидных карточек в файле")
            return False

        return True

    @staticmethod
    def show_popup(title, message):
        CardApp.show_popup(title, message)


if __name__ == '__main__':
    CardApp().run()