import pygame
import sys
import random
import math
from concurrent.futures import ThreadPoolExecutor
import ctypes
import pyautogui
from pygame._sdl2 import Window
import pygetwindow as gw
import win32con
import win32gui

pygame.init()

# Размеры окна
window_width = 200
window_height = 300

# Создаем окно без верхней панели и рамки
window = pygame.display.set_mode((window_width, window_height), pygame.NOFRAME)

drag_window = False
offset_x = 0
offset_y = 0
drag_update_speed = 10  # Limit drag update speed for window movement

# Размеры элементов
element_size = 20

# Загрузка и изменение размера изображений
rock_image = pygame.image.load("rock.png")
rock_image = pygame.transform.scale(rock_image, (element_size, element_size))

scissors_image = pygame.image.load("scissors.png")
scissors_image = pygame.transform.scale(scissors_image, (element_size, element_size))

paper_image = pygame.image.load("paper.png")
paper_image = pygame.transform.scale(paper_image, (element_size, element_size))

# Количество элементов
num_elements = 50

# Положение и скорость элементов
element_x = [random.randint(0, window_width - element_size) for _ in range(num_elements)]
element_y = [random.randint(0, window_height - element_size) for _ in range(num_elements)]
element_speed = [random.uniform(0.2, 0.5) for _ in range(num_elements)]

# Маппинг типов элементов на их индексы (индексы картинок)
type_to_index = {
    "rock": 0,
    "scissors": 1,
    "paper": 2
}

dict_types = {
    0: "rock",
    1: "scissors",
    2: "paper"
}
# Маппинг элементов на их типы ("rock", "scissors", "paper")
element_types = [random.choice(["rock", "scissors", "paper"]) for _ in range(num_elements)]

# Маппинг индексов картинок на сами картинки
element_images = {
    0: rock_image,
    1: scissors_image,
    2: paper_image
}

clock = pygame.time.Clock()


def distance(x1, y1, x2, y2):
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def get_winner(weapon1, weapon2):
    # Функция для определения победителя
    if ((weapon1 == "rock" and weapon2 == "scissors") or (weapon1 == "scissors" and weapon2 == "rock")):
        return 0
    if ((weapon1 == "scissors" and weapon2 == "paper") or (weapon1 == "paper" and weapon2 == "scissors")):
        return 1
    if ((weapon1 == "paper" and weapon2 == "rock") or (weapon1 == "rock" and weapon2 == "paper")):
        return 2
    return -1

def get_nearest_target_and_enemy_index(current_index):
    current_x = element_x[current_index]
    current_y = element_y[current_index]
    min_distance = float('inf')
    nearest_target_index = None
    nearest_enemy_index = None

    current_type = element_types[current_index]
    target_types = {
        "rock": "scissors",
        "paper": "rock",
        "scissors": "paper"
    }
    enemy_types = {
        "rock": "paper",
        "paper": "scissors",
        "scissors": "rock"
    }

    for i in range(num_elements):
        if i != current_index and element_types[i] == target_types[current_type]:
            dist = distance(current_x, current_y, element_x[i], element_y[i])
            if dist < min_distance:
                min_distance = dist
                nearest_target_index = i

        if i != current_index and element_types[i] == enemy_types[current_type]:
            dist = distance(current_x, current_y, element_x[i], element_y[i])
            if dist < min_distance:
                min_distance = dist
                nearest_enemy_index = i

    return [nearest_target_index, nearest_enemy_index]

def check_border(arr_x, arr_y, window_width, window_height, index):
    arr_x[index] = max(arr_x[index], 0)
    arr_y[index] = max(arr_y[index], 0)
    arr_x[index] = min(arr_x[index], window_width - element_size)
    arr_y[index] = min(arr_y[index], window_height - element_size)

# Функция для обновления положения элементов в отдельном потоке
def update_elements(current_index):
    nearest_target_index, nearest_enemy_index = get_nearest_target_and_enemy_index(current_index)
    if (nearest_target_index is not None) or (nearest_enemy_index is not None):
        if nearest_target_index is not None:
            target_x, target_y = element_x[nearest_target_index], element_y[nearest_target_index]

            # Вычисляем вектор движения к цели
            dx = target_x - element_x[current_index]
            dy = target_y - element_y[current_index]
            distance_to_target = distance(element_x[current_index], element_y[current_index], target_x, target_y)

            dx = dx / distance_to_target
            dy = dy / distance_to_target

            # Отталкиваемся от ближайшего врага
            if nearest_enemy_index is not None:
                nearest_enemy_x, nearest_enemy_y = element_x[nearest_enemy_index], element_y[nearest_enemy_index]
                repel_dx = element_x[current_index] - nearest_enemy_x
                repel_dy = element_y[current_index] - nearest_enemy_y
                distance_to_enemy = distance(element_x[current_index], element_y[current_index], nearest_enemy_x, nearest_enemy_y)

                if distance_to_enemy < 20:  # На этом расстоянии элементы начинают отдаляться от опасных врагов
                    repel_dx = repel_dx / distance_to_enemy
                    repel_dy = repel_dy / distance_to_enemy

                    dx += repel_dx
                    dy += repel_dy


            # Обновляем положение элемента с учетом векторов движения и отталкивания
            element_x[current_index] += dx * element_speed[current_index]
            element_y[current_index] += dy * element_speed[current_index]

            # Проверяем, вышли ли за границу
            check_border(element_x, element_y, window_width, window_height, current_index)
            # Проверяем, чтобы элементы двигались вдоль стенок
            if element_x[current_index] == 0 or element_x[current_index] == window_width - element_size:
                dx *= -1
            if element_y[current_index] == 0 or element_y[current_index] == window_height - element_size:
                dy *= -1

            element_x[current_index] += dx * element_speed[current_index]
            element_y[current_index] += dy * element_speed[current_index]
        else:
            # Если у элемента нет цели, двигаем его от ближайшего врага
            # Находим ближайшего врага
            _, nearest_enemy_index = get_nearest_target_and_enemy_index(current_index)
            if nearest_enemy_index is not None:
                # Генерируем случайное направление движения от врага
                enemy_x, enemy_y = element_x[nearest_enemy_index], element_y[nearest_enemy_index]
                dx = element_x[current_index] - enemy_x
                dy = element_y[current_index] - enemy_y

                # Нормализуем вектор движения
                distance_to_target = math.sqrt(dx ** 2 + dy ** 2)
                if distance_to_target > 0:
                    dx /= distance_to_target
                    dy /= distance_to_target
            else:
                # Если нет врага, возвращаем случайное направление
                # Генерируем случайное направление движения
                dx = random.uniform(-1, 1)
                dy = random.uniform(-1, 1)

                # Нормализуем вектор движения
                distance_to_target = math.sqrt(dx ** 2 + dy ** 2)
                if distance_to_target > 0:
                    dx /= distance_to_target
                    dy /= distance_to_target

            element_x[current_index] += dx * element_speed[current_index]
            element_y[current_index] += dy * element_speed[current_index]

            # Проверяем, вышли ли за границу
            check_border(element_x, element_y, window_width, window_height, current_index)
            # Проверяем, чтобы элементы двигались вдоль стенок
            if element_x[current_index] == 0 or element_x[current_index] == window_width - element_size:
                dx *= -1
            if element_y[current_index] == 0 or element_y[current_index] == window_height - element_size:
                dy *= -1

            element_x[current_index] += dx * element_speed[current_index]
            element_y[current_index] += dy * element_speed[current_index]



def check_collapse(current_index):
    for i in range(current_index + 1, num_elements):
        distance_between = distance(element_x[current_index], element_y[current_index], element_x[i], element_y[i])
        if distance_between < element_size:
            # Определяем победителя в соответствии с правилами игры "камень, ножницы, бумага"
            winner_index = get_winner(element_types[current_index], element_types[i])
            if winner_index != -1:
                element_types[current_index] = dict_types[winner_index]
                element_types[i] = dict_types[winner_index]

def check_end_game():
    unique_types = set(element_types)
    if len(unique_types) == 1:
        return True, unique_types.pop()
    return False, None

def display_game_over_screen():
    global element_types, element_x, element_y, element_speed, drag_window, offset_y, offset_x
    game_over_font = pygame.font.Font(None, 25)
    game_over_text = game_over_font.render("Игра окончена!", True, (255, 255, 255))

    game_over_alpha = 0  # Начальная прозрачность слоя
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    drag_window = True
                    # Вычисляем смещение курсора относительно верхнего левого угла окна
                    # offset_x, offset_y = event.pos[0] - window.get_rect().x, event.pos[1] - window.get_rect().y
                    offset_x, offset_y = event.pos[0], event.pos[1]
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    drag_window = False
            if event.type == pygame.USEREVENT:
                # Перезапуск игры
                element_types = [random.choice(["rock", "scissors", "paper"]) for _ in range(num_elements)]
                element_x = [random.randint(0, window_width - element_size) for _ in range(num_elements)]
                element_y = [random.randint(0, window_height - element_size) for _ in range(num_elements)]
                element_speed = [random.uniform(0.2, 0.5) for _ in range(num_elements)]
                pygame.time.set_timer(pygame.USEREVENT, 0)
                return

        if drag_window:
            mouse_x, mouse_y = pyautogui.position()
            # Изменяем позицию окна на основе перемещения курсора
            window_pos_x = int(mouse_x - offset_x)
            window_pos_y = int(mouse_y - offset_y)
            set_window_position(window_pos_x, window_pos_y)

        window.fill((100, 255, 255))

        # Отображение элементов
        for i in range(num_elements):
            element_type = element_types[i]
            if element_type in type_to_index:
                element_index = type_to_index[element_type]
                window.blit(element_images[element_index], (element_x[i], element_y[i]))

        # Создаем поверхность для затемнения экрана
        game_over_surface = pygame.Surface((window_width, window_height))
        game_over_surface.set_alpha(game_over_alpha)  # Устанавливаем прозрачность слоя
        game_over_surface.fill((0, 0, 0))  # Заливаем слой темным цветом
        window.blit(game_over_surface, (0, 0))  # Отрисовываем слой на экране

        # Отображение текста "Игра окончена!"
        window.blit(game_over_text, (window_width // 2 - game_over_text.get_width() // 2,
                                     window_height // 2 - game_over_text.get_height()))

        pygame.display.flip()
        clock.tick(20)  # Устанавливаем низкую частоту обновления экрана

        # Увеличиваем прозрачность слоя с течением времени
        if game_over_alpha < 150:
            game_over_alpha += 10


def set_window_position(x, y):
    # Use ctypes to set the window position
    HWND = pygame.display.get_wm_info()["window"]
    ctypes.windll.user32.SetWindowPos(HWND, 0, x, y, 0, 0, 0x0001)


while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                drag_window = True
                # Вычисляем смещение курсора относительно верхнего левого угла окна
                # offset_x, offset_y = event.pos[0] - window.get_rect().x, event.pos[1] - window.get_rect().y
                offset_x, offset_y = event.pos[0], event.pos[1]
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                drag_window = False

    if drag_window:
        mouse_x, mouse_y = pyautogui.position()
        # Изменяем позицию окна на основе перемещения курсора
        window_pos_x = int(mouse_x - offset_x)
        window_pos_y = int(mouse_y - offset_y)
        set_window_position(window_pos_x, window_pos_y)

    # with ThreadPoolExecutor() as executor:
    #     executor.map(update_elements, range(num_elements))
    #     executor.map(check_collapse, range(num_elements))

    # Обновляем положение элементов и проверяем столкновения
    for i in range(num_elements):
        update_elements(i)
        check_collapse(i)

    # Заливка окна белым цветом
    window.fill((100, 255, 255))

    # Рисуем элементы на экране
    for i in range(num_elements):
        element_type = element_types[i]
        if element_type in type_to_index:
            element_index = type_to_index[element_type]  # Получаем индекс картинки по типу элемента
            window.blit(element_images[element_index], (element_x[i], element_y[i]))

    pygame.display.flip()

    # Устанавливаем окно поверх других окон (в неактивном состоянии)
    hwnd = pygame.display.get_wm_info()["window"]
    win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)

    clock.tick(30)

    # Проверяем конец игры
    is_game_over, winner_type = check_end_game()
    if is_game_over:
        # Запускаем таймер, который вызовет событие pygame.USEREVENT через 5 секунд
        pygame.time.set_timer(pygame.USEREVENT, 5000)  # 5000 миллисекунд (5 секунд)
        display_game_over_screen()


