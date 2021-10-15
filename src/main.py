import pyautogui
import ctypes
from ctypes import wintypes
from PIL import Image
import time
import sys
import os

# --- keyboard input initialization ---
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
            self.wScan = user32.MapVirtualKeyExW(self.wVk,
                                                 MAPVK_VK_TO_VSC, 0)
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
chrhex = {'a':0x41, 'b':0x42, 'c':0x43, 'd':0x44, 'e':0x45, 'f':0x46, 'g':0x47, 'h':0x48, 'i':0x49,
          'j':0x4A, 'k':0x4B, 'l':0x4C, 'm':0x4D, 'n':0x4E, 'o':0x4F, 'p':0x50, 'q':0x51, 'r':0x52,
          's':0x53, 't':0x54, 'u':0x55, 'v':0x56, 'w':0x57, 'x':0x58, 'y':0x59, 'z':0x5A, 'A':0x41,
          'B':0x42, 'C':0x43, 'D':0x44, 'E':0x45, 'F':0x46, 'G':0x47, 'H':0x48, 'I':0x49, 'J':0x4A,
          'K':0x4B, 'L':0x4C, 'M':0x4D, 'N':0x4E, 'O':0x4F, 'P':0x50, 'Q':0x51, 'R':0x52, 'S':0x53,
          'T':0x54, 'U':0x55, 'V':0x56, 'W':0x57, 'X':0x58, 'Y':0x59, 'Z':0x5A, ' ':0x20, '1':0x31,
          '2':0x32, '3':0x33, '4':0x34, '5':0x35, '6':0x36, '7':0x37, '8':0x38, '9':0x39, '0':0x30,
          'enter':0x0D, 'back':0x08, 'left':0x25, 'up':0x26, 'right':0x27, 'down':0x28, 'ctrl':0x11,
          'shift':0x10, 'tab':0x09, 'Capital':0x14, '\\':0xDC, ';':0xBA, '\r':0x0D, '\x08':0x08,
          'Lcontrol': 0xA2, 'Rcontrol': 0xA3, 'Lmenu': 0xA4, 'Rmenu': 0xA5, 'Lwin': 0x5B,
          'Rwin': 0x5C, 'Oem_3': 0xC0, '`': 0xC0, 'volume_mute': 0xAD, 'volume_down': 0xAE,
          'volume_up': 0xAF, 'media_next': 0xB0, 'media_prev':0xB1, 'media_pause': 0xB3,
          'apps': 0x5D, 'snapshot': 0x2C, 'delete': 0x2E, 'Lshift': 0xA0, 'Rshift': 0xA1,
          'pause': 0x13, 'space':0x20, 'escape':0x1B, '.':0xBE, ',':0xBC, '/':0xBF}


def hitkeys(keys, delay=0.001):
    for key in keys:
        presskey(chrhex[key])
        time.sleep(delay)
        releasekey(chrhex[key])
        time.sleep(delay)


class RatioFit:

    def __init__(self, screen_size, ratio, delay):
        self.delay = delay
        x, y = screen_size
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
        self.upgrade_dict = {
            1: ',',
            2: '.',
            3: '/'
        }
        self.monkey_dict = {
            "hero": "u",
            "dart": "q",
            "boomerang": "w",
            "bomb": "e",
            "tack": "r",
            "ice": "t",
            "glue": "y",
            "sniper": "z",
            "sub": "x",
            "boat": "c",
            "plane": "v",
            "heli": "b",
            "mortar": "n",
            "dartling": "m",
            "wizard": "a",
            "super": "s",
            "ninja": "d",
            "alchemist": "f",
            "druid": "g",
            "farm": "h",
            "spikes": "j",
            "village": "k",
            "engineer": "l"
        }
        self.monkeys_placed = []

    def convert_pos(self, rel_pos):
        # return absolute screen position based on relative 0-1 floats
        x = self.offset[0] + rel_pos[0] * self.width
        y = self.offset[1] + rel_pos[1] * self.height
        return x, y

    def revert_pos(self, abs_pos):
        # return the relative position based on absolute position
        x = (abs_pos[0] - self.offset[0]) / self.width
        y = (abs_pos[1] - self.offset[1]) / self.height
        return x, y

    def place(self, monkey, position, delay=0.):
        # place the specified monkey at the specified position
        monkey = monkey.lower()
        self.monkeys_placed.append((monkey, position))
        hitkeys(self.monkey_dict[monkey])
        pyautogui.moveTo(*self.convert_pos(position))
        time.sleep(delay/2)
        pyautogui.click(*self.convert_pos(position))
        time.sleep(delay/2)

    def upgrade(self, monkey_index, path, delay=0.):
        # upgrade the specified monkey into the specified path
        pyautogui.click(*self.convert_pos(self.monkeys_placed[monkey_index][1]))
        time.sleep(delay/2)
        hitkeys(self.upgrade_dict[path])
        time.sleep(delay/2)
        hitkeys(['escape'])

    def ready_to_upgrade(self, path):
        # determines whether the selected monkey is ready to be upgraded into the specified path
        green = self.open_image(r"images\buttons\upgrade.png", other=0)
        spots = list(pyautogui.locateAllOnScreen(green, confidence=0.9))
        heights = [self.revert_pos(pyautogui.center(f))[1] for f in spots]
        if path == 1:
            return any(f < 0.54 for f in heights)
        if path == 2:
            return any(0.54 < f < 0.68 for f in heights)
        if path == 3:
            return any(0.68 < f for f in heights)

    def wait_to_upgrade(self, monkey_index, path, delay=0.):
        # upgrade the specified monkey into the specified path
        # this function simply waits until you have enough money to do so
        if type(path) == int:
            path = [path]
        pyautogui.click(*self.convert_pos(self.monkeys_placed[monkey_index][1]))
        for p in path:
            while not self.ready_to_upgrade(p):
                if self.check_for_level_up():
                    pyautogui.click(*self.convert_pos(self.monkeys_placed[monkey_index][1]))
            time.sleep(delay)
            hitkeys(self.upgrade_dict[p])
            time.sleep(delay)
        hitkeys(['escape'])

    def open_image(self, path, other=1):
        # opens and scales images
        img = Image.open(resource_path(path))
        if other:
            if self.other_ratio != 1:
                img = img.resize((int(img.width * self.other_ratio), int(img.height * self.other_ratio)))
            return img
        if self.image_ratio != 1:
            img = img.resize((int(img.width * self.image_ratio), int(img.height * self.image_ratio)))
        return img

    def open_track(self, track, difficulty):
        # opens the specified track into the specified difficulty from the home screen
        # WILL overwrite saves
        wait_until_click(self.open_image(r"images\buttons\play.png"))
        track_img = self.open_image("images\\buttons\\%s.png" % track)
        time.sleep(1)
        while not click_image(track_img):
            wait_until_click(self.open_image(r"images\buttons\track switch.png"))
            time.sleep(self.delay)
        wait_until_click(self.open_image("images\\buttons\\%s.png" % difficulty))
        wait_until_click(self.open_image(r"images\buttons\begin.png"))
        if shows_up(self.open_image(r"images\edge cases\overwrite.png"), 0.5):
            wait_until_click(self.open_image(r"images\buttons\OK.png"))
        wait_to_see(self.open_image("images\\track confirms\\%s.png" % track, other=0))

    def check_for_level_up(self):
        # function checks if you've leveled up and handles it
        if click_image(self.open_image(r"images\edge cases\LEVEL UP.png")):
            if shows_up(self.open_image(r"images\edge cases\monkey knowledge.png"), 1):
                click_image(self.open_image(r"images\edge cases\monkey knowledge.png"))
            time.sleep(self.delay)
            hitkeys(' ')
            return True
        return False

    def wait_and_check_level(self, secs):
        # function waits a given amount of time, and regularly check if you've leveled up
        if time_left := shows_up(self.open_image(r"images\edge cases\LEVEL UP.png"), secs):
            wait_until_click(self.open_image(r"images\edge cases\LEVEL UP.png"))
            if shows_up(self.open_image(r"images\edge cases\monkey knowledge.png"), 1):
                click_image(self.open_image(r"images\edge cases\monkey knowledge.png"))
            time.sleep(0.3)
            hitkeys(' ')
            time.sleep(time_left)

    def wait_to_finish(self):
        # waits for the round to finish, then goes to the home screen
        next_but = self.open_image(r"images\buttons\NEXT.png")
        while not is_present(next_but):
            self.check_for_level_up()
        time.sleep(self.delay)
        wait_until_click(next_but)
        time.sleep(self.delay)
        wait_until_click(self.open_image(r"images\buttons\home.png"))
        time.sleep(self.delay)
        # special event edge case
        reward = self.open_image(r"images\edge cases\collect.png")
        if shows_up(reward, 10):
            instas = self.open_image(r"images\edge cases\insta monkey.png")
            insta_g = self.open_image(r"images\edge cases\insta monkey green.png")
            insta_b = self.open_image(r"images\edge cases\insta monkey blue.png")
            insta_p = self.open_image(r"images\edge cases\insta monkey purple.png")
            insta_y = self.open_image(r"images\edge cases\insta monkey yellow.png")
            cont = self.open_image(r"images\edge cases\cont.png")
            back = self.open_image("images/edge cases/back.png")
            wait_until_click(reward)
            while not is_present(cont):
                if not any(click_image(f) for f in [instas, insta_g, insta_b, insta_p, insta_y]):
                    time.sleep(1)
                    pyautogui.click(*self.convert_pos((0.5, 0.5)))
                    if click_image(back):
                        break
            if click_image(cont):
                time.sleep(1)
            hitkeys(['escape'])

    def do_command(self, command):
        if type(command) == int:
            time.sleep(command)
        elif type(command) == tuple:
            if type(command[0]) == str and type(command[1]) == str:
                self.open_track(*command)
            elif type(command[0]) == str and type(command[1]) == tuple:
                self.place(command[0], command[1], delay=self.delay)
            elif type(command[0]) == int and type(command[1]) == tuple:
                self.wait_to_upgrade(*command, delay=self.delay)

    def play(self, parameters):
        self.do_command(parameters[0])  # should start the track
        self.do_command(parameters[1])  # should place the first tower
        hitkeys('  ', self.delay)
        for command in parameters[2:]:
            self.do_command(command)
        self.wait_to_finish()


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def is_present(image):
    # function which determines if a certain image is present
    try:
        spot = pyautogui.locateOnScreen(image, confidence=0.85)
    except pyautogui.ImageNotFoundException:  # not necessary with this version I guess
        return False
    if spot is None:
        return False
    return True


def wait_to_see(image):
    # function to pause execution until a particular image appears
    while not is_present(image):
        pass


def click_image(image, delay=0.):
    # function to click an image on screen
    # returns false if image is not on screen
    # returns true if image is successfully clicked
    # will delay by given amount only if button found
    try:
        spot = pyautogui.locateOnScreen(image, confidence=0.85)
    except pyautogui.ImageNotFoundException:  # not necessary with this version I guess
        return False
    if spot is None:
        return False
    coords = pyautogui.center(spot)
    pyautogui.click(*coords)
    time.sleep(delay)
    return True


def wait_until_click(image):
    # function to click on an image, or wait until the image appears and then click on it
    while not click_image(image):
        pass


def shows_up(image, secs):
    # return whether or not a particular image shows up on the screen in a given time interval
    # if it shows up return the remaining amount of time left
    start = time.time()
    while time.time() < start + secs:
        if is_present(image):
            return start + secs - time.time()
    return False


def main():
    # to get out, move mouse to the corner of the screen to trigger the fail safe
    delay = 0.3
    screen = RatioFit(pyautogui.size(), 19/11, delay)
    # menu options
    options = ['monkey meadow (easy)',
               'tree stump (easy)',
               'town center (easy)',
               'the cabin (easy)',
               'flooded valley (easy)']
    # how to play each menu option
    plays = [(("monkey meadow", "easy"),  # choose map
              ("hero", (0.1, 0.5)),  # place tower
              10,  # delay
              ("sniper", (0.8, 0.43)),
              (1, (2, 2, 1, 2, 1))),  # upgrade tower

             (("tree stump", "easy"),
              ("ninja", (0.4, 0.4)),
              (0, (3, 1, 1, 3, 3)),
              15,
              ("ninja", (0.4, 0.31)),
              (1, (3, 1, 1, 3, 1, 1)),
              (0, (3,))),

             (("town center", "easy"),
              ("dart", (0.26, 0.78)),
              (0, (3, 3, 3, 3, 2, 2)),
              15,
              ("dart", (0.18, 0.47)),
              (1, (1, 1, 1, 1, 2, 2)),
              15,
              ("dart", (0.12, 0.65)),
              (2, (3, 3, 3, 3, 2, 2))),

             (("the cabin", "easy"),
              ("boomerang", (0.6, 0.28)),
              (0, (3, 3, 1, 1, 1, 1)),
              10,
              ("sub", (0.54, 0.28)),
              (1, (1, 1, 1)),
              7,
              ("boomerang", (0.6, 0.12)),
              (2, (2, 2, 3, 3, 3, 3))),

             (("flooded valley", "easy"),
              ('boat', (0.5, 0.15)),
              (0, (2, 2, 3, 3, 2)),
              25,
              ('boat', (0.53, 0.73)),
              (1, (2, 2, 1, 1, 1, 1)))]
    mainloop = True
    choice = pyautogui.confirm(text='Choose which map to play repeatedly',
                               title='BTD6 bot ready',
                               buttons=options)
    while mainloop:
        screen.play(plays[options.index(choice)])


if __name__ == "__main__":
    main()
