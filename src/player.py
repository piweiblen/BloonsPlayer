import pyautogui
import threading
import ctypes
from ctypes import wintypes
from PIL import Image
from scipy import ndimage
import shutil
import numpy
import time
import sys
import os
user32 = ctypes.WinDLL('user32', use_last_error=True)

# --- window focus ---
WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

_enum_windows = user32.EnumWindows
_enum_windows.argtypes = (WNDENUMPROC, wintypes.LPARAM)
_enum_windows.restype = wintypes.BOOL

def bring_to_front(window_name):
    hwnds = []
    def windowEnumerationHandler(hwnd, lparam):
        hwnds.append(hwnd)
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

# --- keyboard input ---
user32 = ctypes.WinDLL('user32', use_last_error=True)
INPUT_MOUSE    = 0
INPUT_KEYBOARD = 1
INPUT_HARDWARE = 2
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP       = 0x0002
KEYEVENTF_UNICODE     = 0x0004
KEYEVENTF_SCANCODE    = 0x0008
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


def steam_path():
    """ Get the absolute path to the steam executable"""
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
            if os.path.exists(app_path):
                shutil.rmtree(app_path)
            shutil.copytree(exe_path, app_path)
    except AttributeError:
        # _MEIPASS does not exist when running python code
        app_path = os.path.join(os.path.abspath("."), "data")
    return app_path


def fetch_dict(name):
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


# --- player ---
class BloonsError(Exception):
    pass


class RatioFit:

    def __init__(self):
        self.delay = 0.3
        # calculate the position of the playing field
        ratio = 19/11
        x, y = pyautogui.size()
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
        self.upgrade_dict = {1: ',', 2: '.', 3: '/'}
        self.monkey_dict = fetch_dict("monkey hotkeys")
        self.track_difficulties = fetch_dict("map difficulties")
        self.monkey_prices = fetch_dict("monkey prices")
        self.egg_dict = fetch_dict("egg")
        self.monkey_type = dict()
        self.monkey_place = dict()
        self.hero_name = ''
        self.cur_mode = (None, None)
        self.cur_hero = None
        self.abilities_repeat = []
        self.ab_repeat_on = False
        self.preferences = fetch_dict("preferences")
        self.command_time = time.time()
        # prep vars fo more detailed logging
        self.time_log = [""]
        for f in range(100):
            self.time_log.append(str(f+1))
        self.play_start_time = 0
        self.round_logger = False
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
                self.image_dict[key] = self.open_image(path, other)
        # egg mode
        self.egg_mode = False
        self.in_egg = False

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
        while self.ab_repeat_on:
            current_num = len(self.abilities_repeat)
            for key in self.abilities_repeat:
                hit_key(key)
                time.sleep(1/current_num)

    def update_prefs(self):
        self.preferences = fetch_dict("preferences")

    def add_repeat_key(self, key):
        key = str(key)
        self.abilities_repeat.append(key)
        if not self.ab_repeat_on:
            self.ab_repeat_on = True
            newt = threading.Thread(target=self.timer_hit, daemon=True)
            newt.start()

    def remove_repeat_key(self, key):
        key = str(key)
        if key in self.abilities_repeat:
            self.abilities_repeat.remove(key)
        if not self.abilities_repeat:
            self.ab_repeat_on = False

    def cancel_repeat_keys(self, *args):
        self.abilities_repeat = []
        self.ab_repeat_on = False

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
                # bugfix: when the taken screenshot has the cursor in it, the target image is likely not recognised
                pyautogui.moveTo((10, 10))
                return False
        else:
            location = pyautogui.locateCenterOnScreen(image, confidence=confidence)
            if location is not None:
                self.image_pos_dict[image_name] = location
                pyautogui.click(*location)
                return True
            else:
                return False

    def wait_until_click(self, image):
        while not click_image(image):
            self.check_edge_cases(time_only=True)

    def move_to(self, pos_x, pos_y, duration=0):
        position = (float(pos_x), float(pos_y))
        duration = float(duration)
        converted_pos = self.convert_pos(position)
        pyautogui.moveTo(*converted_pos, duration)

    def click(self, pos_x, pos_y, delay=0.):
        position = (float(pos_x), float(pos_y))
        converted_pos = self.convert_pos(position)
        pyautogui.moveTo(*converted_pos)
        time.sleep(delay/2)
        pyautogui.click(*converted_pos)
        time.sleep(delay/2)

    def remove_obstacle(self, pos_x, pos_y):
        self.click(pos_x, pos_y)
        while not click_image(self.image_dict["buttons obstacle"]):
            if self.check_edge_cases():
                self.click(pos_x, pos_y)

    def place(self, monkey, pos_x, pos_y, name, no_delay=False):
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
            if self.cur_mode[0] == "easy":
                price = int(5 * round(0.85 * base_price / 5))
            elif self.cur_mode[1] == "impoppable":
                price = int(5 * round(1.2 * base_price / 5))
            elif self.cur_mode[0] == "hard":
                price = int(5 * round(1.08 * base_price / 5))
            else:
                price = base_price
            if base_price:
                self.wait_for_cash(price)
        # now place
        monkey = monkey.lower()
        position = (float(pos_x), float(pos_y))
        self.monkey_type[name] = monkey
        self.monkey_place[name] = position
        if monkey == 'hero':
            self.hero_name = name
        bring_to_front('BloonsTD6')
        hit_keys(self.monkey_dict[monkey])
        self.click(*position, delay=0.04)

    def get_numbers(self):
        # return the amount of cash the player has as an integer
        top_left = self.convert_pos((0, 0.02))
        bottom_right = self.convert_pos((1, 0.065))
        h = 50
        cropped = pyautogui.screenshot().crop(top_left+bottom_right)
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
                if new_arr.size > 300 and new_arr.shape[0] > 20:
                    spot = pos_insert(hors, min(ys))
                    sections.insert(spot, new_arr)
        nums = []
        last_pos = 0
        cur_num = ""
        for i in range(len(sections)):
            guesses = []
            for f in range(10):
                num_img = self.image_dict['numbers %s' % f].resize(sections[i].shape[::-1]).convert('L')
                match_arr = numpy.array(num_img)
                guesses.append(abs(sections[i] - match_arr).sum() / match_arr.size)
            num = min(range(10), key=lambda x: guesses[x])
            if guesses[num] < 42:
                if hors[i] - last_pos > 43 and cur_num:
                    nums.append(int(cur_num))
                    cur_num = ""
                cur_num += str(num)
                last_pos = hors[i]
        if cur_num:
            nums.append(int(cur_num))
        return nums

    def log_round_times(self):
        # first wait until wee see any round number and set that as the first round
        next_round = 0
        while self.round_logger:
            nums = self.get_numbers()
            if len(nums) > 2:
                next_round = nums[2]
                break
            time.sleep(0.1)
        last_time = self.play_start_time
        # then just log times each time the round ticks up
        while self.round_logger:
            nums = self.get_numbers()
            if len(nums) > 2 and nums[2] == next_round:
                now = time.time()
                secs = round(now - last_time, 1)
                last_time = now
                to_add = str(secs % 60).zfill(2)
                if secs > 60:
                    mns = secs // 60
                    to_add = str(mns % 60).zfill(2) + ":" + to_add
                    if mns > 60:
                        to_add = str(mns // 60).zfill(2) + ":" + to_add
                self.time_log[next_round] += to_add
                next_round += 1
                file = open(os.path.join(data_dir(), "log\\times.csv"), 'w')
                file.write('\n'.join(self.time_log))
                file.close()
            time.sleep(1)

    def ready_to_upgrade(self, path):
        # determines whether the selected monkey is ready to be upgraded into the specified path
        green = self.image_dict["buttons upgrade"]
        spots = list(pyautogui.locateAllOnScreen(green, confidence=0.9))
        heights = [self.revert_pos(pyautogui.center(f))[1] for f in spots]
        if path == 1:
            return any(f < 0.54 for f in heights)
        if path == 2:
            return any(0.54 < f < 0.68 for f in heights)
        if path == 3:
            return any(0.68 < f for f in heights)

    def ready_to_upgrade_hero(self):
        # determines whether a hero is ready to be upgraded
        green = self.image_dict["buttons hero upgrade"]
        spot = pyautogui.locateOnScreen(green, confidence=0.9)
        if spot is None:
            return False
        coords = pyautogui.center(spot)
        x = int(coords[0])
        y = int(coords[1])
        return pyautogui.pixelMatchesColor(x, y, (100, 210, 0), tolerance=20)

    def wait_to_upgrade(self, monkey_name, *path):
        # upgrade the specified monkey into the specified path
        # this function simply waits until you have enough money to do so
        log(": ")
        position = self.convert_pos(self.monkey_place[monkey_name])
        path = [int(p) for p in path]
        bring_to_front('BloonsTD6')
        pyautogui.click(*position)  # select monkey
        if monkey_name == self.hero_name:
            if len(path) == 1:
                num = path[0]
            else:
                num = len(path)
            for f in range(num):
                while not self.ready_to_upgrade_hero():
                    if self.check_edge_cases():
                        pyautogui.click(*position)
                time.sleep(self.delay)
                bring_to_front('BloonsTD6')
                hit_keys(self.upgrade_dict[1])
                log(self.upgrade_dict[1])
                time.sleep(self.delay)
        else:
            if type(path) == int:
                path = [path]
            for p in path:
                while not self.ready_to_upgrade(p):
                    if self.check_edge_cases():
                        pyautogui.click(*position)
                time.sleep(self.delay)
                bring_to_front('BloonsTD6')
                hit_keys(self.upgrade_dict[p])
                log(self.upgrade_dict[p])
                time.sleep(self.delay)
        bring_to_front('BloonsTD6')
        hit_key('escape')

    def change_targeting(self, monkey_name, times, x_place=None, y_place=None):
        times = int(times)
        position = self.convert_pos(self.monkey_place[monkey_name])
        bring_to_front('BloonsTD6')
        pyautogui.click(*position)  # select monkey
        time.sleep(0.15)
        for f in range(times):
            hit_key('tab')
            time.sleep(0.15)
        if self.monkey_type[monkey_name] == "dartling":
            time.sleep(self.delay)
            if x_place is not None and y_place is not None:
                if click_image(self.image_dict["edge cases locked"]):
                    self.click(x_place, y_place)
        if self.monkey_type[monkey_name] == "mortar":
            if x_place is not None and y_place is not None:
                self.click(x_place, y_place)
        hit_key('escape')

    def toggle_priority(self, monkey_name):
        position = self.convert_pos(self.monkey_place[monkey_name])
        bring_to_front('BloonsTD6')
        pyautogui.click(*position)  # select monkey
        hit_key('page_down')
        hit_key('escape')

    def sell_tower(self, monkey_name):
        position = self.convert_pos(self.monkey_place[monkey_name])
        bring_to_front('BloonsTD6')
        pyautogui.click(*position)  # select monkey
        hit_key('back')

    def select_hero(self, scale, inner=False):
        skins = []
        for img in self.image_dict:
            if img.startswith("heroes ") and self.cur_hero in img:
                skins.append(self.image_dict[img])
        scaled_skins = []
        for img in skins:
            scaled_skins.append(img.resize((int(img.width * scale), int(img.height * scale))))
        if not any_present(scaled_skins):
            if inner:
                self.wait_until_click(self.image_dict["heroes change"])
            else:
                self.wait_until_click(self.image_dict["heroes heroes"])
            while not any(click_image(img) for img in skins):
                time.sleep(0.3)
            if shows_up(self.image_dict["heroes select"], 2):
                self.wait_until_click(self.image_dict["heroes select"])
            hit_key('escape')

    def open_track(self, track, difficulty, mode, hero=None):
        # opens the specified track into the specified difficulty from the home screen
        # WILL overwrite saves
        self.cur_mode = (difficulty, mode)
        if track == "none":
            # this is for testing and allows to play the sequence without selecting the map or hero, it just sets everything for the normal workflow to work
            self.cur_hero

        play_button = self.image_dict["buttons play"]
        while not is_present(play_button):
            click_image(self.image_dict["edge cases start"])
            self.collect_reward()
        if hero is not None:  # select the correct hero if specified
            self.cur_hero = hero
            self.select_hero(0.9)
        else:
            self.cur_hero = None
        self.wait_and_static_click(play_button)
        arrow_count = 0
        if "buttons %s" % self.track_difficulties[track] not in self.image_pos_dict:
            time.sleep(1)
        if self.egg_mode:
            egg_img = self.image_dict["edge cases easter bonus"]
            while 1:
                if not self.click_fixed("buttons expert"):
                    click_image(play_button)

                time.sleep(2)
                pos = pyautogui.locateCenterOnScreen(egg_img, confidence=0.8)
                if pos is None:
                    continue
                else:
                    best_dist = 0
                    best_track = None
                    for track in self.egg_dict:
                        t_pos = pyautogui.locateCenterOnScreen(self.image_dict["tracks %s" % track], confidence=0.6)
                        if t_pos is not None and t_pos[0] < pos[0]:
                            new_dist = (t_pos[0] - pos[0])**2 + (t_pos[1] - pos[1])**2
                            if best_track is None or new_dist < best_dist:
                                best_track = track
                                best_dist = new_dist
                    if best_track is None:
                        continue
                    self.egg_mode = best_track
                    self.in_egg = True
                    self.click_fixed("tracks %s" % best_track, confidence=0.6)
                    log("\nopen " + best_track)
                    time.sleep(1)
                    if is_present(self.image_dict["buttons %s" % difficulty]):
                        egg_path = os.path.join(data_dir(), "tas", self.egg_dict[best_track])
                        file = open(egg_path)
                        self.egg_mode = tuple(file.read().split('\n'))
                        file.close()
                        open_args = parse_args(self.egg_mode[0], "open")
                        if len(open_args) > 3:
                            self.cur_hero = open_args[3]
                            self.select_hero(0.52, inner=True)
                        track, difficulty, mode = open_args[:3]
                        self.cur_mode = (difficulty, mode)
                        break
        else:
            while not self.click_fixed("tracks %s" % track):
                if not self.click_fixed("buttons %s" % self.track_difficulties[track]):
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
            self.wait_until_click(self.image_dict["buttons OK"])
            time.sleep(1)
        if mode in ["chimps", "impoppable", "deflation"]:
            self.wait_until_click(self.image_dict["buttons OK"])
            time.sleep(2)
            return None
        if mode == "apopalypse":
            self.wait_and_static_click(self.image_dict["edge cases apop play"])
            time.sleep(1)
            return None
        while not is_loading():  # make sure we see the loading screen
            pass
        while is_loading():  # wait for the loading screen
            pass
        time.sleep(self.delay)

    def check_edge_cases(self, time_only=False):
        # function checks for and handles various edge cases
        # first check if we've leveled up
        if not time_only and click_image(self.image_dict["edge cases LEVEL UP"]):
            log("\nLevel up")
            if shows_up(self.image_dict["edge cases monkey knowledge"], 10):
                click_image(self.image_dict["edge cases monkey knowledge"])
            time.sleep(self.delay)
            hit_keys('  ', 0.5)
            return True
        # then check for tas failure
        if not time_only and is_present(self.image_dict["edge cases restart"]):
            if self.preferences["screenshot"]:
                self.wait_until_click(self.image_dict["edge cases review"])
                time.sleep(1)
                cur_time = time.strftime("%Y-%m-%d-%H-%M-%S")
                log("\nScreenshot taken "+cur_time)
                pyautogui.screenshot(os.path.join(data_dir(), "log", cur_time+".png"))
                hit_key("escape")
            self.cancel_repeat_keys()
            self.wait_until_click(self.image_dict["buttons home"])
            raise BloonsError("TAS Failed")
        # then check for the game having crashed (1 hour since last command)
        if self.preferences["crash protection"] and self.preferences["steam path"]:
            if time.time() - self.command_time > 3600 or not bring_to_front('BloonsTD6'):
                log("\nGame crashed")
                self.command_time = time.time()
                os.system("TASKKILL /F /IM bloonstd6.exe")
                time.sleep(10)
                self.launch_bloons()
                self.wait_until_click(self.image_dict["edge cases start"])
                raise BloonsError("TAS Failed")
        return False

    def wait_and_check_edges(self, secs):
        # function waits a given amount of time, and regularly check if you've leveled up
        secs = float(secs)
        start = time.time()
        while time.time() < start + secs:
            self.check_edge_cases()

    def wait_for_lives(self, lives):
        # wait for amount of lives to drop to or below given number
        lives = float(lives)
        while 1:
            nums = self.get_numbers()
            if len(nums) > 0 and nums[0] <= lives:
                break
            self.check_edge_cases()

    def wait_for_cash(self, money):
        # wait for amount of cash to reach given number
        money = float(money)
        while 1:
            nums = self.get_numbers()
            time.sleep(1)
            if len(nums) > 1 and nums[1] >= money:
                break
            self.check_edge_cases()

    def wait_for_round(self, round_num):
        # wait to reach given round
        round_num = float(round_num)
        while 1:
            nums = self.get_numbers()
            if len(nums) > 2 and nums[2] >= round_num:
                break
            self.check_edge_cases()

    def collect_reward(self):
        reward = self.image_dict["edge cases collect"]
        if is_present(reward):
            log('\ncollect rewards')
            instas = self.image_dict["edge cases insta monkey"]
            insta_g = self.image_dict["edge cases insta monkey green"]
            insta_b = self.image_dict["edge cases insta monkey blue"]
            insta_p = self.image_dict["edge cases insta monkey purple"]
            insta_y = self.image_dict["edge cases insta monkey yellow"]
            cont = self.image_dict["edge cases cont"]
            back = self.image_dict["edge cases back"]
            self.wait_until_click(reward)
            while not is_present(cont):
                if not any(click_image(f) for f in [instas, insta_g, insta_b, insta_p, insta_y]):
                    self.check_edge_cases()
                    time.sleep(1)
                    pyautogui.click(*self.convert_pos((0.5, 0.5)))
                    if click_image(back):
                        break
            if click_image(cont):
                time.sleep(1)
            hit_key('escape')

    def wait_to_finish(self):
        # waits for the round to finish, then goes to the home screen
        next_but = self.image_dict["buttons NEXT"]
        while not is_present(next_but):
            click_image(self.image_dict["buttons insta-monkey"])  # for chimps/impoppable
            self.check_edge_cases()
        time.sleep(self.delay)
        self.wait_until_click(next_but)
        self.cancel_repeat_keys()
        time.sleep(self.delay)
        home = self.image_dict["buttons home"]
        reward = self.image_dict["edge cases collect"]
        play_button = self.image_dict["buttons play"]
        self.static_click_and_confirm(home, [reward, play_button])
        time.sleep(self.delay)
        # special event edge case
        self.collect_reward()

    def do_command(self, command):
        # interpret and execute a command
        self.command_time = time.time()
        # first do a bit of cleanup
        if '#' in command:
            command = command[:command.index('#')]
        command = command.strip().lower()
        log('\n' + command)
        # define and execute command types
        opts = {"open": self.open_track,
                "place": self.place,
                "upgrade": self.wait_to_upgrade,
                "delay": self.wait_and_check_edges,
                "money": self.wait_for_cash,
                "round": self.wait_for_round,
                "lives": self.wait_for_lives,
                "click": self.click,
                "move": self.move_to,
                "use ability": hit_key,
                "repeat ability": self.add_repeat_key,
                "stop ability": self.remove_repeat_key,
                "stop all abilities": self.cancel_repeat_keys,
                "target": self.change_targeting,
                "priority": self.toggle_priority,
                "sell": self.sell_tower,
                "remove": self.remove_obstacle,
                "change speed": lambda *x: hit_key(' ')}
        for prefix in opts:
            if parse(command, prefix, opts[prefix]):
                break
        else:
            log('\nUnknown command ' + command)

    def start_round(self):
        log('\nStart (hit space twice)')
        hit_keys('  ', self.delay)

    def play(self, parameters):
        if self.egg_mode and not self.in_egg:
            self.run_egg_mode()
            return None
        # play a map once given a list of commands
        self.monkey_place = dict()  # clear out monkey dicts
        self.monkey_type = dict()
        self.play_start_time = time.time()
        if not self.in_egg:
            self.do_command(parameters[0])  # should open the track
        if self.preferences["log times"]:
            # begin logging times if that option was selected
            for f in range(len(self.time_log)):
                self.time_log[f] += ','
            self.time_log[0] += time.strftime("%m/%d/%Y %H:%M:%S")
            self.round_logger = True
            newt = threading.Thread(target=self.log_round_times, daemon=True)
            newt.start()
        start = 2
        if any("start round" in p for p in parameters):
            for i, param in enumerate(parameters[1:]):
                if "start round" in param:
                    start += i
                    break
                self.do_command(param)
        else:
            self.do_command(parameters[1])  # should place the first tower

        # start round if not in apopalypse
        if "apopalypse" not in parameters[0]:
            self.start_round()

        for command in parameters[start:]:
            self.do_command(command)
            time.sleep(self.delay)
        log('\n' + 'Waiting for track to finish, ')
        log(time.strftime("%m/%d/%Y, %H:%M:%S"))
        self.wait_to_finish()

    def run_egg_mode(self):
        try:
            self.open_track("dark castle", "easy", "standard")
            self.play(self.egg_mode)
        except BloonsError:
            raise
        finally:
            self.in_egg = False

    def kill_threads(self):
        self.cancel_repeat_keys()
        self.round_logger = False
        # halt until the other threads die
        while threading.active_count() != 1:
            pass

    def launch_bloons(self):
        if not bring_to_front('BloonsTD6'):
            os.system('"%s" steam://rungameid/960090' % self.preferences["steam path"])

    def wait_and_static_click(self, image, threshold=4):
        # wait for an image to appear, then click when it is not moving
        prev_spot = (0, -9000)
        spot = (-9000,  0)
        while (spot[0]-prev_spot[0])**2 + (spot[1]-prev_spot[1])**2 > threshold:
            location = pyautogui.locateCenterOnScreen(image, confidence=0.85)
            if location is not None:
                prev_spot = spot
                spot = location
            self.check_edge_cases()
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
                self.check_edge_cases()
            if any_present(confirm_images):
                break
            self.check_edge_cases()
            pyautogui.click(*spot)


def is_present(image):
    # function which determines if a certain image is present
    spot = pyautogui.locateOnScreen(image, confidence=0.85)
    return spot is not None


def any_present(images):
    # function which determines if any image from a given list is present
    for image in images:
        if is_present(image):
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


def log_file():
    # get path to log file
    return os.path.join(data_dir(), "log\\log.txt")


def clear_log():
    # empty the log file
    file = open(log_file(), 'w')
    file.close()


def log(txt):
    # add the given text to the log file
    file = open(log_file(), 'a')
    file.write(txt)
    file.close()


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
