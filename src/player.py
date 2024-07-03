import pyautogui
import threading
import ctypes
from ctypes import wintypes
from PIL import Image
from scipy import ndimage
import logging
import shutil
import numpy
import time
import sys
import os
logging.basicConfig(filename=None, level=logging.ERROR, format='%(message)s')
user32 = ctypes.WinDLL('user32', use_last_error=True)

# --- window focus ---
WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

_enum_windows = user32.EnumWindows
_enum_windows.argtypes = (WNDENUMPROC, wintypes.LPARAM)
_enum_windows.restype = wintypes.BOOL

def bring_to_front(window_name):
    hwnds = []
    def windowEnumerationHandler(hwnd, lparam):
        hwnds.append(hwnd & 0x00000000FFFFFFFF)
        return True
    func = WNDENUMPROC(windowEnumerationHandler)
    _enum_windows(func, 0)
    for hwnd in hwnds:
        length = user32.GetWindowTextLengthW(hwnd)
        buff_text = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buff_text, length + 1)
        if window_name == buff_text.value:
            user32.ShowWindow(hwnd, 5)
            user32.SetForegroundWindow(hwnd)
            return True
    return False

def window_is_open(window_name):
    hwnds = []
    def windowEnumerationHandler(hwnd, lparam):
        hwnds.append(hwnd & 0x00000000FFFFFFFF)
        return True
    func = WNDENUMPROC(windowEnumerationHandler)
    _enum_windows(func, 0)
    for hwnd in hwnds:
        length = user32.GetWindowTextLengthW(hwnd)
        buff_text = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buff_text, length + 1)
        if window_name == buff_text.value:
            return True
    return False


# --- keyboard input ---
user32 = ctypes.WinDLL('user32', use_last_error=True)
INPUT_MOUSE    = 0
INPUT_KEYBOARD = 1
INPUT_HARDWARE = 2
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP       = 0x0002
KEYEVENTF_UNICODE     = 0x0004
KEYEVENTF_SCANCODE    = 0x0008
MOUSEEVENTF_MOVE = 0x0001  # mouse move
MOUSEEVENTF_LEFTDOWN = 0x0002  # left button down
MOUSEEVENTF_LEFTUP = 0x0004  # left button up
MOUSEEVENTF_RIGHTDOWN = 0x0008  # right button down
MOUSEEVENTF_RIGHTUP = 0x0010  # right button up
MOUSEEVENTF_MIDDLEDOWN = 0x0020  # middle button down
MOUSEEVENTF_MIDDLEUP = 0x0040  # middle button up
MOUSEEVENTF_WHEEL = 0x0800  # wheel button rolled
MOUSEEVENTF_ABSOLUTE = 0x8000  # absolute move
SM_CXSCREEN = 0
SM_CYSCREEN = 1
MAPVK_VK_TO_VSC = 0
VK_TAB  = 0x09
VK_MENU = 0x12
# C struct definitions
wintypes.ULONG_PTR = wintypes.WPARAM
class MOUSEINPUT(ctypes.Structure):
    _fields_ = (("dx",          wintypes.LONG),
                ("dy",          wintypes.LONG),
                ("mouseData",   wintypes.DWORD),
                ("dwFlags",     wintypes.DWORD),
                ("time",        wintypes.DWORD),
                ("dwExtraInfo", wintypes.ULONG_PTR))
class KEYBDINPUT(ctypes.Structure):
    _fields_ = (("wVk",         wintypes.WORD),
                ("wScan",       wintypes.WORD),
                ("dwFlags",     wintypes.DWORD),
                ("time",        wintypes.DWORD),
                ("dwExtraInfo", wintypes.ULONG_PTR))
    def __init__(self, *args, **kwds):
        super(KEYBDINPUT, self).__init__(*args, **kwds)
        # some programs use the scan code even if KEYEVENTF_SCANCODE
        # isn't set in dwFflags, so attempt to map the correct code.
        if not self.dwFlags & KEYEVENTF_UNICODE:
            self.wScan = user32.MapVirtualKeyExW(self.wVk, MAPVK_VK_TO_VSC, 0)
class HARDWAREINPUT(ctypes.Structure):
    _fields_ = (("uMsg",    wintypes.DWORD),
                ("wParamL", wintypes.WORD),
                ("wParamH", wintypes.WORD))
class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = (("ki", KEYBDINPUT),
                    ("mi", MOUSEINPUT),
                    ("hi", HARDWAREINPUT))
    _anonymous_ = ("_input",)
    _fields_ = (("type",   wintypes.DWORD),
                ("_input", _INPUT))
LPINPUT = ctypes.POINTER(INPUT)
def _check_count(result, func, args):
    if result == 0:
        raise ctypes.WinError(ctypes.get_last_error())
    return args
user32.SendInput.errcheck = _check_count
user32.SendInput.argtypes = (wintypes.UINT, # nInputs
                             LPINPUT,       # pInputs
                             ctypes.c_int)  # cbSize

def presskey(hexKeyCode):
    x = INPUT(type=INPUT_KEYBOARD,
              ki=KEYBDINPUT(wVk=hexKeyCode))
    user32.SendInput(1, ctypes.byref(x), ctypes.sizeof(x))

def releasekey(hexKeyCode):
    x = INPUT(type=INPUT_KEYBOARD,
              ki=KEYBDINPUT(wVk=hexKeyCode,
                            dwFlags=KEYEVENTF_KEYUP))
    user32.SendInput(1, ctypes.byref(x), ctypes.sizeof(x))

def movemouse(x_pos, y_pos):
    # re-implement failsafe
    pos = pyautogui.position()
    sz = pyautogui.size()
    if pos[0] in [0, sz[0]] and pos[1] in [0, sz[1]]:
        raise pyautogui.FailSafeException("PyAutoGUI fail-safe triggered")
    x_calc = int(65536 * x_pos / user32.GetSystemMetrics(SM_CXSCREEN) + 1)
    y_calc = int(65536 * y_pos / user32.GetSystemMetrics(SM_CYSCREEN) + 1)
    x = INPUT(type=INPUT_MOUSE,
              mi=MOUSEINPUT(dx=x_calc, dy=y_calc, dwFlags=MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE))
    user32.SendInput(1, ctypes.byref(x), ctypes.sizeof(x))


def steam_path():
    """ Get the absolute path to the steam executable """
    pf = os.getenv("PROGRAMFILES")
    if pf is None:
        return None
    path = os.path.join(pf, r"Steam\steam.exe")
    if os.path.exists(path):
        return path
    return None


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # _MEIPASS does not exist when running python code
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def data_dir():
    """ Get absolute path to data, points to a folder in AppData/Roaming for the executable """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        exe_path = os.path.join(sys._MEIPASS, "data")
        app_path = os.path.join(os.getenv('APPDATA'), "BloonsPlayer", "data")
        # create appdata directory if it does not exist
        if not os.path.exists(app_path):
            shutil.copytree(exe_path, app_path)
        # update appdata directory if it is out of date
        file = open(os.path.join(exe_path, "version.txt"))
        exe_version = file.read()
        file.close()
        file = open(os.path.join(app_path, "version.txt"))
        app_version = file.read()
        file.close()
        if exe_version != app_version:
            old_prefs = fetch_dict(os.path.join(app_path, "dicts\\preferences.txt"), abs_path=True)
            shipped_prefs = fetch_dict(os.path.join(exe_path, "dicts\\preferences.txt"), abs_path=True)
            if os.path.exists(app_path):
                shutil.rmtree(app_path)
            shutil.copytree(exe_path, app_path)
            for p in shipped_prefs:
                if p in ["filters"]:
                    pass  # do not save this preference
                if p in old_prefs:
                    shipped_prefs[p] = old_prefs[p]
            save_dict("preferences", shipped_prefs)
    except AttributeError:
        # _MEIPASS does not exist when running python code
        app_path = os.path.join(os.path.abspath("."), "data")
    return app_path


def fetch_dict(name, abs_path=False):
    if abs_path:
        file = open(name)
    else:
        file = open(os.path.join(data_dir(), "dicts", name+".txt"))
    ret_val = eval(file.read())
    file.close()
    return ret_val


def save_dict(name, dictionary):
    file = open(os.path.join(data_dir(), "dicts", name+".txt"), 'w')
    file.write("{\n"+",\n".join(f.__repr__()+": "+dictionary[f].__repr__() for f in dictionary)+"\n}")
    file.close()


chrhex = fetch_dict("keycodes")


def hit_keys(keys, delay=0.001):
    for key in keys:
        presskey(chrhex[key])
        time.sleep(delay)
        releasekey(chrhex[key])
        time.sleep(delay)


def hit_key(key, delay=0.001):
    hit_keys([key], delay=delay)


# --- errors ---
class MenuBackError(Exception):
    pass


class BloonsError(Exception):
    pass


class PremieError(Exception):
    pass


# --- thread handler ---
class ThreadHandler:

    def __init__(self):
        self.running = []
        self.thread_history = []

    def begin(self, func):
        if func in self.running:
            return False
        self.running.append(func)

        def wrapper():
            while func in self.running:
                func()

        newt = threading.Thread(target=wrapper, daemon=True)
        newt.start()
        self.thread_history.append(newt)
        return True

    def end(self, func):
        if func not in self.running:
            return False
        self.running.remove(func)
        return True

    def end_all(self):
        self.running = []

    def is_running(self, func):
        return func in self.running

    def any_running(self):
        return any(f.is_alive() for f in self.thread_history)


# --- player ---
class RatioFit:

    def __init__(self, scsz=None):
        self.delay = 0.3
        self.menu_halt = False
        # calculate the position of the playing field
        ratio = 19/11
        if scsz is None:
            x, y = pyautogui.size()
        else:
            x, y = scsz
        log(f"screen size: {(x, y)}")
        if x / y == ratio:
            self.offset = (0, 0)
            self.width = x
            self.height = y
        elif x / y > ratio:
            proper_x = 2 * ((y * ratio) // 2)
            self.offset = ((x - proper_x) // 2, 0)
            self.width = proper_x
            self.height = y
        elif y / x < ratio:
            proper_y = 2 * ((x / ratio) // 2)
            self.offset = (0, (y - proper_y) // 2)
            self.width = x
            self.height = proper_y
        self.image_ratio = self.width / 1920
        self.other_ratio = y / 1200
        # account for sidebar
        sidebar_ratio = 7/30
        self.width -= y * sidebar_ratio
        # account for accounting for the sidebar
        golden_ratio = ratio - sidebar_ratio  # more like 3/2
        self.width_mod = self.width / (self.height * golden_ratio)
        # initialize player variables
        self.threader = ThreadHandler()
        self.scripts = {}
        self.command_dict = {"use ability": hit_key,
                             "change speed": lambda *x: hit_key(' ')}
        prefix = "TAS_"
        for func in dir(self):
            if func.startswith(prefix):
                name = func[len(prefix):].replace("_", " ")
                self.command_dict[name] = getattr(self, func)
        self.upgrade_dict = {1: ',', 2: '.', 3: '/'}
        self.monkey_dict = fetch_dict("monkey hotkeys")
        self.track_difficulties = fetch_dict("map difficulties")
        self.monkey_prices = fetch_dict("monkey prices")
        self.gerry_dict = fetch_dict("gerry shop")
        self.monkey_type = dict()
        self.monkey_place = dict()
        self.hero_name = ''
        self.cur_mode = (None, None)
        self.cur_hero = None
        self.abilities_repeat = []
        self.pause_keys = False
        self.pause_mouse = False
        self.move_args = []
        self.preferences = fetch_dict("preferences")
        self.edge_case = 0
        self.rpc = None
        self.script_name = ""
        self.large_img = ""
        self.start_time = time.time()
        self.command_time = time.time()
        # prep vars fo more detailed logging
        self.time_log = [""]
        for f in range(100):
            self.time_log.append(str(f+1))
        self.play_start_time = 0
        self.round_logger = False
        self.log_round = None
        self.log_time = 0
        # open and convert all images
        self.image_pos_dict = {}
        self.image_dict = {}
        base_path = resource_path("images\\")
        for folder in os.listdir(base_path):
            for image in os.listdir(os.path.join(base_path, folder)):
                img_name = image[:image.rfind('.')]
                if folder == "buttons" and img_name == "upgrade":
                    other = 0
                else:
                    other = 1
                key = str(folder)+' '+str(img_name)
                path = os.path.join(base_path, folder, image)
                self.image_dict[key.lower()] = self.open_image(path, other)
        # preprocess tracks
        for name in self.image_dict:
            if name.startswith('tracks'):
                cropped = self.image_dict[name].point(lambda p: p > 254 and 255)
                cropped = cropped.convert('L').point(lambda p: p > 254 and 255)
                self.image_dict[name] = self.image_dict[name].crop(cropped.getbbox())
        # egg
        self.default_egg = None

    def convert_pos(self, rel_pos):
        # return absolute screen position based on relative 0-1 floats
        x = (rel_pos[0] - 0.5) / self.width_mod + 0.5
        x = self.offset[0] + x * self.width
        y = self.offset[1] + rel_pos[1] * self.height
        return x, y

    def revert_pos(self, abs_pos):
        # return the relative position based on absolute position
        x = (abs_pos[0] - self.offset[0]) / self.width
        y = (abs_pos[1] - self.offset[1]) / self.height
        x = (x - 0.5) * self.width_mod + 0.5
        return x, y

    def timer_hit(self):
        current_num = len(self.abilities_repeat)
        if not current_num:
            time.sleep(0.1)
        for key in self.abilities_repeat:
            if not self.pause_keys:
                hit_key(key)
            time.sleep(1/current_num)

    def update_prefs(self):
        self.preferences = fetch_dict("preferences")

    def TAS_repeat_ability(self, key):
        # add the specified key to the list of repeated abilities
        key = str(key)
        self.abilities_repeat.append(key)
        self.threader.begin(self.timer_hit)

    def TAS_stop_ability(self, key):
        key = str(key)
        if key in self.abilities_repeat:
            self.abilities_repeat.remove(key)
        if not self.abilities_repeat:
            self.threader.end(self.timer_hit)

    def TAS_stop_all_abilities(self, *args):
        self.abilities_repeat = []
        self.threader.end(self.timer_hit)

    def open_image(self, path, other):
        # opens and scales images
        img = Image.open(resource_path(path))
        if other:
            if self.other_ratio != 1:
                img = img.resize((int(img.width * self.other_ratio), int(img.height * self.other_ratio)))
            return img
        if self.image_ratio != 1:
            img = img.resize((int(img.width * self.image_ratio), int(img.height * self.image_ratio)))
        return img

    def click_fixed(self, image_name, confidence=0.85):
        # high performance way to click an image which only ever appears in one location on screen
        # return true if clicked, return false if not present
        image = self.image_dict[image_name]
        if confidence == 0:
            if image_name in self.image_pos_dict:
                known_pos = self.image_pos_dict[image_name]
                pyautogui.click(*known_pos)
                return True
            else:
                confidence = 0.85
        if image_name in self.image_pos_dict:
            known_pos = self.image_pos_dict[image_name]
            w = image.width * 13 // 10
            h = image.height * 13 // 10
            region = (known_pos[0] - w//2, known_pos[1] - h//2, w, h)
            section = pyautogui.screenshot(region=region)
            if pyautogui.locate(image, section, confidence=confidence) is not None:
                pyautogui.click(*known_pos)
                return True
            else:
                movemouse(10, 10)
                return False
        else:
            location = pyautogui.locateCenterOnScreen(image, confidence=confidence)
            if location is not None:
                self.image_pos_dict[image_name] = location
                pyautogui.click(*location)
                return True
            else:
                movemouse(10, 10)
                return False

    def wait_until_click(self, image):
        while not click_image(image):
            self.check_edge_cases(time_only=True)

    def TAS_move(self, duration, *args):
        # move the cursor to the specified location(s) over the specified duration
        # backwards compatibility for no duration specified
        if len(args) == 1:
            args = (duration,) + args
            duration = 0
        duration = float(duration)
        positions = []
        fps = 60
        for f in range(0, len(args)-1, 2):
            positions.append(numpy.array(self.convert_pos((float(args[f]), float(args[f+1])))))
        total_dist = 0
        if len(positions) == 0:  # no positions
            return None
        if duration < 1 / fps:
            for position in positions:
                movemouse(*position)
            return None
        if len(positions) == 1:  # one position so add
            positions.insert(0, numpy.array(pyautogui.position()))
        for f in range(1, len(positions)):
            total_dist += numpy.linalg.norm(positions[f] - positions[f-1])
        if total_dist == 0:
            return None
        for f in range(1, len(positions)):
            this_dist = numpy.linalg.norm(positions[f] - positions[f-1])
            steps = int(fps * duration * this_dist / total_dist)
            for g in range(steps):
                if not self.pause_mouse:
                    pos = (g * positions[f] + (steps - g) * positions[f-1]) / steps
                    movemouse(*pos)
                time.sleep(1 / fps)

    def move_rep(self):
        self.TAS_move(*self.move_args)

    def TAS_repeat_move(self, duration, *args):
        self.pause_mouse = False
        self.move_args = (duration, *args)
        self.threader.begin(self.move_rep)

    def TAS_stop_move(self, *args):
        self.threader.end(self.move_rep)

    def TAS_click(self, pos_x, pos_y, delay=0):
        position = (float(pos_x), float(pos_y))
        converted_pos = self.convert_pos(position)
        self.pause_mouse = True
        time.sleep(delay/2)
        movemouse(*converted_pos)
        time.sleep(delay/2)
        pyautogui.click(*converted_pos)
        self.pause_mouse = False

    def TAS_remove(self, pos_x, pos_y):
        self.TAS_click(pos_x, pos_y)
        while not click_image(self.image_dict["buttons obstacle"]):
            if self.check_edge_cases():
                self.TAS_click(pos_x, pos_y)

    def convert_price(self, base_price):
        if self.cur_mode[0] == "easy":
            return int(5 * round(0.85 * base_price / 5))
        elif self.cur_mode[1] == "impoppable":
            return int(5 * round(1.2 * base_price / 5))
        elif self.cur_mode[0] == "hard":
            return int(5 * round(1.08 * base_price / 5))
        else:
            return base_price

    def TAS_place(self, monkey, pos_x, pos_y, name, no_delay=False):
        # place the specified monkey at the specified position
        # first wait for enough money
        if not no_delay:
            base_price = 0
            if monkey == "hero":
                if self.cur_hero is not None:
                    for m in self.monkey_prices:
                        if self.cur_hero in m:
                            base_price = self.monkey_prices[m]
            else:
                base_price = self.monkey_prices[monkey]
            self.TAS_money(self.convert_price(base_price))
        # now place it
        self.pause_keys = True
        monkey = monkey.lower()
        position = (float(pos_x), float(pos_y))
        self.monkey_type[name] = monkey
        self.monkey_place[name] = position
        if monkey == 'hero':
            self.hero_name = name
        bring_to_front('BloonsTD6')
        hit_key(self.monkey_dict[monkey])
        self.TAS_click(*position, delay=0.04)
        self.pause_keys = False

    def TAS_gerry_shop(self, item, *args):
        try:
            item = max([f for f in self.gerry_dict if item in f], key=len)
        except ValueError:
            log(f'invalid gerry item "{item}" specified')
        images = [f for f in self.image_dict if f.startswith(f"gerry shop {item}")]
        info = self.gerry_dict[item]
        self.TAS_click(*self.monkey_place[self.hero_name])  # select gerry
        time.sleep(0.3)  # let menu pop out
        self.click_image("gerry shop open")  # enter shop if we aren't in it
        if "no delay" not in args:  # wait for enough money
            self.TAS_money(self.convert_price(info["price"]))
        while not any(self.click_image(img) for img in images):  # select item
            if self.check_edge_cases():
                self.TAS_click(*self.monkey_place[self.hero_name])  # reselect gerry if unclicked
            self.click_image("gerry shop open")
        self.TAS_move(0, 0.5, 0.5)
        time.sleep(0.3)

        def attempt_position(pos_args):
            try:
                self.TAS_click(float(pos_args[0]), float(pos_args[1]))
                return True
            except ValueError:
                log("invalid geraldo item syntax: invalid position literal")
                return False
            except IndexError:
                log("invalid geraldo item syntax: missing positional argument(s)")
                return False

        for i in [1]:  # not the best way to code this but
            if info["type"] == "tower":
                if attempt_position(args[:2]):
                    if len(args) > 2:
                        self.monkey_type[args[2]] = "gerry item"
                        self.monkey_place[args[2]] = (float(args[0]), float(args[1]))
                    break
            elif info["type"] == "hurdle":
                if attempt_position(args[:2]):
                    break
            elif info["type"] == "buff":
                if item == "pet rabbit":  # rabbit always goes to gerry
                    self.TAS_click(*self.monkey_place[self.hero_name])
                    break
                # take the first arg which is a monkey name, if any are
                names = [arg for arg in args if arg in self.monkey_place]
                if names:
                    self.TAS_click(*self.monkey_place[names[0]])
                    break
                # we'll try to see if a position is given as a backup
                if attempt_position(args[:2]):
                    break
        else:
            self.TAS_click(0.5, 0.5)  # default shot in the dark when all else fails
        time.sleep(0.3)
        hit_key('escape')

    def TAS_toggle_autostart(self, *args):
        hit_key('escape')
        time.sleep(0.6)
        for f in range(3):
            if not (self.click_image("misc autostart off") or self.click_image("misc autostart on")):
                break
        else:
            log("toggle autostart failed")
        hit_key('escape')

    def TAS_start_round(self, *args):
        fast = True
        if args and args[0] == "slow":
            fast = False
        hit_key(' ')
        if fast:
            time.sleep(self.delay)
            hit_key(' ')

    def TAS_send_rounds(self, num):
        for f in range(int(num)):
            self.click_fixed("buttons round advance")
            time.sleep(1/30)

    def get_numbers(self):
        return self.get_numbers_from_img(pyautogui.screenshot())

    def get_numbers_from_img(self, img):
        # return the amount of cash the player has as an integer
        top_left = self.convert_pos((0, 0.02))  # TODO: let func truly accept any image
        bottom_right = self.convert_pos((1, 0.065))
        h = 75
        cropped = img.crop(top_left+bottom_right)
        cropped = cropped.resize((int(h * cropped.width / cropped.height), h))
        cropped = cropped.point(lambda p: p > 254 and 255)
        cropped = cropped.convert('L').point(lambda p: p > 254 and 255)
        cropped = cropped.crop(cropped.getbbox())
        sections = []
        hors = []
        labels, l_num = ndimage.label(numpy.array(cropped))
        for f in range(1, l_num+1):
            new_arr = 255 * (labels == f)
            xs, ys = numpy.where(new_arr != 0)
            if xs.size > 0 and ys.size > 0:
                new_arr = new_arr[min(xs):max(xs)+1, min(ys):max(ys)+1]
                if new_arr.size > (h**2)/10 and new_arr.shape[0] > h/2:
                    spot = pos_insert(hors, min(ys))
                    sections.insert(spot, new_arr)
        nums = []
        last_pos = 0
        cur_num = ""
        for i in range(len(sections)):
            guesses = []
            for f in range(11):
                num_img = self.image_dict['numbers %s' % f].resize(sections[i].shape[::-1]).convert('L')
                match_arr = numpy.array(num_img)
                guesses.append(abs(sections[i] - match_arr).sum() / match_arr.size)
            num = min(range(11), key=lambda x: guesses[x])
            if guesses[num] < (h**2)/50:
                if (hors[i] - last_pos > 75 or num > 9) and cur_num:
                    nums.append(int(cur_num))
                    cur_num = ""
                if num < 10:
                    cur_num += str(num)
                last_pos = hors[i]
        if cur_num:
            nums.append(int(cur_num))
        return nums

    def log_round_times(self):
        if not self.log_round:
            nums = self.get_numbers()
            if len(nums) > 2:
                self.log_round = nums[2]
            self.log_time = self.play_start_time
            time.sleep(0.1)
        else:
            nums = self.get_numbers()
            #if len(nums) > 2 and nums[2] not in (self.log_round, self.log_round-1):
            #    log(f"Erroneous round read {nums} last valid round {self.log_round-1}")
            if len(nums) > 2 and nums[2] == self.log_round:
                now = time.time()
                secs = round(now - self.log_time, 1)
                self.log_time = now
                to_add = str(secs % 60).zfill(2)
                if secs > 60:
                    mns = secs // 60
                    to_add = str(mns % 60).zfill(2) + ":" + to_add
                    if mns > 60:
                        to_add = str(mns // 60).zfill(2) + ":" + to_add
                self.time_log[self.log_round] += to_add
                self.log_round += 1
                file = open(os.path.join(data_dir(), "log\\times.csv"), 'w')
                file.write('\n'.join(self.time_log))
                file.close()
            time.sleep(1)

    def ready_to_upgrade(self, path):
        # determines whether the selected monkey is ready to be upgraded into the specified path
        green = self.image_dict["buttons upgrade"]
        spots = list(pyautogui.locateAllOnScreen(green, confidence=0.9))
        spots = [self.revert_pos(pyautogui.center(f)) for f in spots]
        heights = [f[1] for f in spots]
        if path == 1:
            ret = any(f < 0.54 for f in heights)
        if path == 2:
            ret = any(0.54 < f < 0.68 for f in heights)
        if path == 3:
            ret = any(0.68 < f for f in heights)
        if ret:
            to_log = []
            for f in spots:
                if not any(abs(g[0]-f[0])+abs(g[1]-f[1]) < 0.01 for g in to_log):
                    to_log.append(f)
            log(f"{time.time():.3f}", end=': ')
            log([(f"{f[0]:.3f}", f"{f[1]:.3f}") for f in to_log])
        return ret

    def ready_to_upgrade_hero(self):
        # determines whether a hero is ready to be upgraded
        if self.cur_hero in "geraldo":
            self.click_image("gerry shop close")
        green = self.image_dict["buttons hero upgrade"]
        spots = [spot for spot in pyautogui.locateAllOnScreen(green, confidence=0.9) if self.revert_pos(spot)[1] > 0.5]
        if not spots:
            return False
        coords = pyautogui.center(spots[0])
        x = int(coords[0])
        y = int(coords[1])
        return pyautogui.pixelMatchesColor(x, y, (100, 210, 0), tolerance=20)

    def TAS_upgrade(self, monkey_name, *path):
        # upgrade the specified monkey into the specified path
        # this function simply waits until you have enough money to do so
        position = self.monkey_place[monkey_name]
        path = [int(p) for p in path]
        bring_to_front('BloonsTD6')
        self.TAS_click(*position)  # select monkey
        if monkey_name == self.hero_name:
            if len(path) == 1:
                path = path[0] * [1]
            else:
                path = len(path) * [1]
        for p in path:
            while 1:
                if self.cur_mode[1] == "sandbox":
                    break  # we have infinite money, don't bother checking
                if monkey_name == self.hero_name:
                    if self.ready_to_upgrade_hero():
                        break
                else:
                    if self.ready_to_upgrade(p):
                        break
                if self.check_edge_cases():
                    self.TAS_click(*position)
            time.sleep(self.delay)
            bring_to_front('BloonsTD6')
            hit_keys(self.upgrade_dict[p])
            log(self.upgrade_dict[p])
            time.sleep(self.delay)
        log('')
        bring_to_front('BloonsTD6')
        hit_key('escape')

    def TAS_target(self, monkey_name, times, x_place=None, y_place=None):
        # change the targeting of the specified tower
        times = int(times)
        bring_to_front('BloonsTD6')
        self.TAS_click(*self.monkey_place[monkey_name])  # select monkey
        time.sleep(0.15)
        for f in range(times):
            hit_key('tab')
            time.sleep(0.15)
        if self.monkey_type[monkey_name] == "dartling":
            time.sleep(self.delay)
            if x_place is not None and y_place is not None:
                if click_image(self.image_dict["edge cases locked"]):
                    self.TAS_click(x_place, y_place)
        if self.monkey_type[monkey_name] == "mortar":
            if x_place is not None and y_place is not None:
                self.TAS_click(x_place, y_place)
        hit_key('escape')

    def TAS_priority(self, monkey_name, x_place=None, y_place=None):
        # toggle the priority of the specified tower
        bring_to_front('BloonsTD6')
        self.TAS_click(*self.monkey_place[monkey_name])  # select monkey
        hit_key('page_down')
        if x_place is not None and y_place is not None:
                self.TAS_click(x_place, y_place)
        hit_key('escape')

    def TAS_sell(self, monkey_name):
        # sell the specified tower
        bring_to_front('BloonsTD6')
        self.TAS_click(*self.monkey_place[monkey_name])  # select monkey
        hit_key('back')
        del self.monkey_place[monkey_name]
        del self.monkey_type[monkey_name]

    def select_hero(self, scale, inner=False):
        skins = []
        for img in self.image_dict:
            if img.startswith("heroes ") and self.cur_hero in img:
                skins.append(self.image_dict[img])
        scaled_skins = []
        for img in skins:
            scaled_skins.append(img.resize((int(img.width * scale), int(img.height * scale))))
        if not any_present(scaled_skins, confidence=0.85):
            if inner:
                self.wait_until_click(self.image_dict["heroes change"])
            else:
                self.wait_until_click(self.image_dict["heroes heroes"])
            while not any(click_image(img) for img in skins):
                time.sleep(0.3)
                self.check_edge_cases(time_only=True)
            if shows_up(self.image_dict["heroes select"], 2):
                self.wait_until_click(self.image_dict["heroes select"])
            hit_key('escape')

    def egg_open(self, egg_type):
        play_button = self.image_dict["buttons play"]
        while not is_present(play_button):
            self.check_edge_cases(time_only=True)
            click_image(self.image_dict["edge cases start"])
            self.collect_reward()
        click_image(play_button)
        time.sleep(self.delay)
        if type(egg_type) == str:
            egg_types = [egg_type]
        else:
            egg_types = egg_type
        egg_metas = [fetch_dict('egg meta')[egg_type] for egg_type in egg_types]
        egg_dicts = [fetch_dict(egg_meta["dict"]) for egg_meta in egg_metas]
        dif_button = "buttons " + egg_metas[0]["difficulty"]  # does not support multi-difficulty searches
        egg_imgs = [self.image_dict[f"edge cases {egg_type} bonus"] for egg_type in egg_types]
        i = 0
        while 1:
            i += 1
            if not self.click_fixed(dif_button):
                click_image(play_button)
            time.sleep(2)
            if i > 5 or self.default_egg not in egg_types:
                inds = range(len(egg_types))
            else:
                inds = [egg_types.index(self.default_egg)]
            for f in inds:
                pos = pyautogui.locateCenterOnScreen(egg_imgs[f], confidence=0.8)
                if pos is None:
                    continue
                best_dist = 0
                best_track = None
                for track in egg_dicts[f]:
                    t_pos = pyautogui.locateCenterOnScreen(self.image_dict["tracks %s" % track], confidence=0.85)
                    if t_pos is not None and t_pos[0] < pos[0] and t_pos[1] < pos[1]:
                        new_dist = (t_pos[0] - pos[0])**2 + (t_pos[1] - pos[1])**2
                        if best_track is None or new_dist < best_dist:
                            best_track = track
                            best_dist = new_dist
                if best_track is None:
                    log("track not found")
                    continue
                # track selected
                self.default_egg = egg_types[f]
                self.script_name = egg_dicts[f][best_track][:-4]
                return self.scripts[egg_dicts[f][best_track]]
            self.check_edge_cases(time_only=True)

    def open_race(self, track, difficulty, mode, hero=None):
        self.cur_mode = (difficulty, mode)
        self.cur_hero = hero
        menu_button = self.image_dict["buttons race menu"]
        race_button = self.image_dict["buttons race"]
        while not any_present((menu_button, race_button)):
            self.check_edge_cases(time_only=True)
            click_image(self.image_dict["edge cases start"])
            self.collect_reward()
        # no need to select hero since race hero is fixed
        while not click_image(race_button):
            click_image(menu_button)
        self.wait_until_click(self.image_dict["buttons ok"])
        time.sleep(1.5)
        # no need to ensure autostart for race either

    def TAS_open(self, track, difficulty, mode, hero=None):
        # opens the specified track into the specified difficulty from the home screen
        # WILL overwrite saves
        self.cur_mode = (difficulty, mode)
        self.cur_hero = hero
        if track == "race":
            self.open_race(track, difficulty, mode, hero)
            return None
        play_button = self.image_dict["buttons play"]
        dif_button = "buttons %s" % self.track_difficulties[track]
        while not any_present((play_button, self.image_dict[dif_button])):
            self.check_edge_cases(time_only=True)
            click_image(self.image_dict["edge cases start"])
            self.collect_reward()
        if hero is not None:  # select the correct hero if specified
            if is_present(self.image_dict[dif_button]):
                self.select_hero(0.52, inner=True)
            else:
                self.select_hero(0.8)
        # self.wait_and_static_click(play_button)  # taking this out so that one can start from maps menu
        arrow_count = 0
        if dif_button not in self.image_pos_dict:
            time.sleep(1)
        while not self.click_fixed("tracks %s" % track):
            self.check_edge_cases(time_only=True)
            if not self.click_fixed(dif_button):
                click_image(play_button)
            else:
                arrow_count += 1
            if arrow_count > 3*11:
                # we've scrolled the whole menu 3 times, lower the confidence threshold
                if self.click_fixed("tracks %s" % track, confidence=0.6):
                    time.sleep(1)
                    if is_present(self.image_dict["buttons %s" % difficulty]):
                        break
        self.wait_until_click(self.image_dict["buttons %s" % difficulty])
        self.wait_until_click(self.image_dict["buttons %s" % mode])
        if shows_up(self.image_dict["edge cases overwrite"], 0.5):
            self.wait_until_click(self.image_dict["buttons ok"])
            time.sleep(1)
        if mode in ["chimps", "impoppable", "deflation", "sandbox"]:
            self.wait_until_click(self.image_dict["buttons ok"])
            time.sleep(2)
        elif mode == "apopalypse":
            self.wait_and_static_click(self.image_dict["edge cases apop play"])
            time.sleep(1)
        else:
            while not is_loading():  # make sure we see the loading screen
                self.check_edge_cases(time_only=True)
            while is_loading():  # wait for the loading screen
                self.check_edge_cases(time_only=True)
            time.sleep(self.delay)
        if self.preferences['ensure autostart']:
            hit_key('escape')
            self.pause_mouse = True
            time.sleep(1)
            click_image(self.image_dict["misc autostart off"])
            self.pause_mouse = False
            hit_key('escape')

    def check_edge_cases(self, time_only=False):
        # function checks for and handles various edge cases
        # check if menu says we should stop
        if self.menu_halt:
            self.menu_halt = False
            raise MenuBackError("Go back to the menu")
        if not time_only:
            self.edge_case = (self.edge_case + 1) % 4
            if self.edge_case == 0:
                # collect round 100 insta if present
                click_image(self.image_dict["buttons insta-monkey"])
            if self.edge_case == 1:
                # check if we finished prematurely
                next_but = self.image_dict["buttons next"]
                vict_but = self.image_dict["edge cases victory"]
                if any_present((next_but, vict_but)):
                    raise PremieError("Script succeeded prematurely")
            if self.edge_case == 2:
                # check if we've leveled up
                if click_image(self.image_dict["edge cases level up"]):
                    log("Level up")
                    if shows_up(self.image_dict["edge cases monkey knowledge"], 10):
                        click_image(self.image_dict["edge cases monkey knowledge"])
                    time.sleep(self.delay)
                    hit_keys('  ', 0.5)
                    return True
            if self.edge_case == 3:
                # then check for tas failure
                if any_present((self.image_dict["edge cases restart"], self.image_dict["edge cases defeat"])):
                    self.kill_threads()
                    if self.preferences["screenshot"]:
                        self.wait_until_click(self.image_dict["edge cases review"])
                        time.sleep(1)
                        cur_time = time.strftime("%Y-%m-%d-%H-%M-%S")
                        log("Screenshot taken "+cur_time)
                        log("Numbers read "+repr(self.get_numbers()))
                        pyautogui.screenshot(os.path.join(data_dir(), "log", "screenshot "+cur_time+".png"))
                        hit_key("escape")
                    self.TAS_stop_all_abilities()
                    self.wait_until_click(self.image_dict["buttons home"])
                    raise BloonsError("TAS Failed")
        # then check for the game having crashed (1 hour since last command)
        if self.preferences["crash protection"] and self.preferences["steam path"]:
            if time.time() - self.command_time > 3600 or not window_is_open('BloonsTD6'):
                self.kill_threads()
                log("Game crashed ", end='')
                log(time.strftime("%m/%d/%Y, %H:%M:%S"))
                self.command_time = time.time()
                os.system("TASKKILL /F /IM bloonstd6.exe")
                time.sleep(10)
                self.launch_bloons()
                while not click_image(self.image_dict["edge cases start"]):
                    pass
                raise BloonsError("TAS Failed")
        return False

    def TAS_delay(self, secs):
        # function waits a given amount of time, and regularly check if you've leveled up
        secs = float(secs)
        start = time.time()
        while time.time() < start + secs:
            self.check_edge_cases()

    def TAS_lives(self, lives):
        # wait for amount of lives to drop to or below given number
        lives = float(lives)
        while 1:
            nums = self.get_numbers()
            if len(nums) > 0 and nums[0] <= lives:
                break
            self.check_edge_cases()

    def TAS_money(self, money):
        # wait for amount of cash to reach given number
        if not money:
            return None
        money = float(money)
        while 1:
            nums = self.get_numbers()
            time.sleep(1)
            if len(nums) > 1 and nums[1] >= money:
                break
            self.check_edge_cases()

    def TAS_round(self, round_num):
        # wait to reach given round
        round_num = float(round_num)
        while 1:
            nums = self.get_numbers()
            if len(nums) > 2 and nums[2] >= round_num:
                break
            self.check_edge_cases()

    def collect_reward(self):
        # collect event rewards if they are present
        reward = self.image_dict["edge cases collect"]
        if is_present(reward):
            log('collecting rewards')
            insta_monkey = self.image_dict["buttons insta-monkey"]
            insta_colors = [self.image_dict["edge cases insta monkey white"],
                            self.image_dict["edge cases insta monkey green"],
                            self.image_dict["edge cases insta monkey blue"],
                            self.image_dict["edge cases insta monkey purple"],
                            self.image_dict["edge cases insta monkey yellow"]]
            cont = self.image_dict["edge cases cont"]
            back = self.image_dict["edge cases back"]
            self.wait_until_click(reward)
            while not click_image(back):
                if not any(click_image(f) for f in [cont, reward, insta_monkey] + insta_colors):
                    self.check_edge_cases(time_only=True)
                    time.sleep(1)

    def wait_to_finish(self):
        # waits for the round to finish, then goes to the home screen
        next_but = self.image_dict["buttons next"]
        vict_but = self.image_dict["edge cases victory"]
        while not any_present((next_but, vict_but)):
            try:
                self.check_edge_cases()
            except PremieError:
                break
        time.sleep(self.delay)
        self.kill_threads()
        click_image(next_but)
        time.sleep(self.delay)
        home = self.image_dict["buttons home"]
        reward = self.image_dict["edge cases collect"]
        play_button = self.image_dict["buttons play"]
        self.static_click_and_confirm(home, [reward, play_button])
        time.sleep(self.delay)
        # special event edge case
        self.collect_reward()

    def do_command(self, command):
        if self.rpc is not None:
            self.rpc.update(pid=os.getpid(), details=self.script_name, state=command,
                            start=self.start_time, large_image=self.large_img, large_text="map",
                            small_image="techbot", small_text="bot")
        # interpret and execute a command
        self.command_time = time.time()
        # first do a bit of cleanup
        if '#' in command:
            command = command[:command.index('#')]
        command = command.strip().lower()
        log(command)
        # execute command types
        for prefix in self.command_dict:
            if parse(command, prefix, self.command_dict[prefix]):
                break
        else:
            log('Unknown command ' + command)

    def play(self, parameters):
        self.start_time = time.time()
        # play a map once given a list of commands
        self.monkey_place = dict()  # clear out monkey dicts
        self.monkey_type = dict()
        self.play_start_time = time.time()
        map_name = parse_args(parameters[0], "open")[0]
        self.large_img = map_name.replace(' ', '_').replace("'", '_')
        self.do_command(parameters[0])  # should open the track
        if self.preferences["log times"]:
            # begin logging times if that option was selected
            self.log_round = None
            for f in range(len(self.time_log)):
                self.time_log[f] += ','
            self.time_log[0] += time.strftime("%m/%d/%Y %H:%M:%S")
            self.threader.begin(self.log_round_times)
        self.do_command(parameters[1])  # should place the first tower
        if not (any("start round" in p for p in parameters) or "deflation" in parameters[0]):
            # if no start round command, start on our own
            log('Start (hit space twice)')
            if "apopalypse" in parameters[0]:  # apopalypse runs on its own
                hit_keys(' ', self.delay)
            else:
                hit_keys('  ', self.delay)
        for command in parameters[2:]:
            try:
                self.do_command(command)
                time.sleep(self.delay)
            except PremieError:
                log('Track finished prematurely')
                break
        log('Waiting for track to finish: ', end='')
        log(time.strftime("%F, %T"))
        if self.rpc is not None:
            self.rpc.update(pid=os.getpid(), details=self.script_name, state="Waiting to finish",
                            start=self.start_time, large_image=self.large_img, large_text="map",
                            small_image="techbot", small_text="bot")
        self.wait_to_finish()

    def run_egg_mode(self, egg_type):
        if self.rpc is not None:
            self.rpc.update(pid=os.getpid(), details=f'bonus hunting mode', state="finding rewards",
                            start=self.start_time, large_image="collection", large_text="collection",
                            small_image="techbot", small_text="bot")
        script = self.egg_open(egg_type)
        self.play(script)

    def kill_threads(self):
        self.TAS_stop_all_abilities()
        self.TAS_stop_move()
        self.threader.end_all()
        # halt until the other threads die
        while self.threader.any_running():
            pass

    def launch_bloons(self):
        if not bring_to_front('BloonsTD6'):
            os.system('"%s" steam://rungameid/960090' % self.preferences["steam path"])
        time.sleep(7)

    def wait_and_static_click(self, image, threshold=4, timeout=0):
        # wait for an image to appear, then click when it is not moving
        prev_spot = (0, -9000)
        spot = (-9000,  0)
        start_time = time.time()
        while (spot[0]-prev_spot[0])**2 + (spot[1]-prev_spot[1])**2 > threshold:
            location = pyautogui.locateCenterOnScreen(image, confidence=0.85)
            if location is not None:
                prev_spot = spot
                spot = location
            self.check_edge_cases()
            if timeout and time.time() - start_time > timeout:
                return False
        pyautogui.click(*spot)

    def static_click_and_confirm(self, image, confirm_images, threshold=4):
        # function to click an image on screen
        # makes sure the image is not moving when clicked
        # will continue to click image until confirmation image is seen
        if type(confirm_images) != list:
            confirm_images = [confirm_images]
        while True:
            prev_spot = (0, -9000)
            spot = (-9000,  0)
            while (spot[0]-prev_spot[0])**2 + (spot[1]-prev_spot[1])**2 > threshold:
                location = pyautogui.locateCenterOnScreen(image, confidence=0.85)
                if location is not None:
                    prev_spot = spot
                    spot = location
                if any_present(confirm_images):
                    break
                self.check_edge_cases(time_only=True)
            if any_present(confirm_images):
                break
            self.check_edge_cases(time_only=True)
            pyautogui.click(*spot)

    def click_image(self, img_name):
        self.pause_keys = True
        ret_val = click_image(self.image_dict[img_name])
        self.pause_keys = False
        return ret_val


def is_present(image, confidence=0.85):
    # function which determines if a certain image is present
    spot = pyautogui.locateOnScreen(image, confidence=confidence)
    return spot is not None


def any_present(images, confidence=0.85):
    # function which determines if any image from a given list is present
    for image in images:
        if is_present(image, confidence=confidence):
            return True
    return False


def click_image(image, delay=0.):
    # function to click an image on screen
    # returns boolean indicating if image was found
    # will delay by given amount only if button found
    coords = pyautogui.locateCenterOnScreen(image, confidence=0.85)
    if coords is None:
        return False
    pyautogui.click(*coords)
    time.sleep(delay)
    return True


def shows_up(image, secs):
    # return if a particular image shows up on the screen in a given time interval
    # if it shows up return the remaining amount of time left
    start = time.time()
    while time.time() < start + secs:
        if is_present(image):
            return start + secs - time.time()
    return False


def is_loading():
    # checks if the loading screen is being shown
    screen = pyautogui.screenshot()
    pixel_count = screen.width * screen.height
    black = 0
    for pixel in screen.getdata():
        if pixel == (0, 0, 0):
            black += 1
    return bool(black/pixel_count > 0.5)


def create_log_file():
    path = os.path.join(data_dir(), "log")
    new_file = os.path.join(path, "log " + time.strftime("%Y-%m-%d-%H-%M-%S") + ".txt")
    if not os.path.exists(new_file):  # create new log file
        open(new_file, "w").close()
    return new_file


def log_file():
    # get path to log file
    path = os.path.join(data_dir(), "log")
    last_log = ""
    for file in sorted(os.listdir(path)):
        if file.startswith("log"):
            last_log = file
    if not last_log:
        return create_log_file()
    return os.path.join(path, last_log)


def log(txt, end='\n'):
    # add the given text to the log file
    if not isinstance(txt, str):
        try:
            txt = str(txt)
        except:
            txt = "Failed to convert data to str"
    txt += end
    logging.info(txt)
    with open(log_file(), 'a') as file:
        file.write(txt)


def parse_args(command, prefix):
    if '#' in command:
        command = command[:command.index('#')]
    command = command.strip().lower()
    if not command.startswith(prefix):
        return []
    sub_command = command[len(prefix):]
    return [c.strip("( )") for c in sub_command.split(',')]


def parse(command, prefix, func):
    args = parse_args(command, prefix)
    if not args:
        return False
    func(*args)
    return True


def pos_insert(lis, n):
    # insert n into sorted list lis, return position inserted
    min_p = 0
    max_p = len(lis)
    ind = (max_p + min_p) // 2
    while min_p < max_p:
        if lis[ind] < n:
            min_p = ind + 1
        else:
            max_p = ind
        ind = (max_p + min_p) // 2
    lis.insert(ind, n)
    return ind
