import pyautogui
import tkinter
import ctypes
from ctypes import wintypes
from PIL import Image
import math
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
        # open and convert all images
        self.image_dict = {}
        base_path = resource_path("images\\")
        for folder in os.listdir(base_path):
            if folder == "track confirms":
                other_b = 0
            else:
                other_b = 1
            for image in os.listdir(os.path.join(base_path, folder)):
                if folder == "buttons" and image == "upgrade.png":
                    other = 0
                else:
                    other = other_b
                self.image_dict[str(folder)+' '+str(image)] = self.open_image(os.path.join(base_path, folder, image),
                                                                              other=other)

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

    def ready_to_upgrade(self, path):
        # determines whether the selected monkey is ready to be upgraded into the specified path
        green = self.image_dict["buttons upgrade.png"]
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
        log(": ")
        if type(path) == int:
            path = [path]
        pyautogui.click(*self.convert_pos(self.monkeys_placed[monkey_index][1]))
        for p in path:
            while not self.ready_to_upgrade(p):
                if self.check_for_level_up():
                    pyautogui.click(*self.convert_pos(self.monkeys_placed[monkey_index][1]))
            time.sleep(delay)
            hitkeys(self.upgrade_dict[p])
            log(self.upgrade_dict[p])
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

    def open_track(self, track, difficulty, mode):
        # opens the specified track into the specified difficulty from the home screen
        # WILL overwrite saves
        play_button = self.image_dict["buttons play.png"]
        arrow_button = self.image_dict["buttons track switch.png"]
        track_img = self.image_dict["buttons %s.png" % track]
        track_confirm = self.image_dict["track confirms %s.png" % track]
        static_click_and_confirm(play_button, arrow_button)
        while not click_image(track_img):
            if is_present(arrow_button):
                wait_until_click(arrow_button)
                time.sleep(self.delay)
            elif is_present(play_button):
                wait_until_click(play_button)
        wait_until_click(self.image_dict["buttons %s.png" % difficulty])
        wait_until_click(self.image_dict["buttons %s.png" % mode])
        if shows_up(self.image_dict["edge cases overwrite.png"], 0.5):
            wait_until_click(self.image_dict["buttons OK.png"])
        if mode in ["chimps", "impoppable"]:
            wait_until_click(self.image_dict["buttons OK.png"])
            time.sleep(1)
        if mode == "apopalypse":
            apop_okay = self.image_dict["edge cases apop play.png"]
            static_click_and_confirm(apop_okay, track_confirm)
        wait_to_see(track_confirm)

    def check_for_level_up(self):
        # function checks if you've leveled up and handles it
        if click_image(self.image_dict["edge cases LEVEL UP.png"]):
            if shows_up(self.image_dict["edge cases monkey knowledge.png"], 1):
                click_image(self.image_dict["edge cases monkey knowledge.png"])
            time.sleep(self.delay)
            hitkeys(' ')
            return True
        return False

    def wait_and_check_level(self, secs):
        # function waits a given amount of time, and regularly check if you've leveled up
        if time_left := shows_up(self.image_dict["edge cases LEVEL UP.png"], secs):
            wait_until_click(self.image_dict["edge cases LEVEL UP.png"])
            if shows_up(self.image_dict["edge cases monkey knowledge.png"], 1):
                click_image(self.image_dict["edge cases monkey knowledge.png"])
            time.sleep(self.delay)
            hitkeys(' ')
            time.sleep(time_left)

    def wait_to_finish(self):
        # waits for the round to finish, then goes to the home screen
        next_but = self.image_dict["buttons NEXT.png"]
        while not is_present(next_but):
            self.check_for_level_up()
        time.sleep(self.delay)
        wait_until_click(next_but)
        time.sleep(self.delay)
        home = self.image_dict["buttons home.png"]
        reward = self.image_dict["edge cases collect.png"]
        play_button = self.image_dict["buttons play.png"]
        static_click_and_confirm(home, [reward, play_button])
        time.sleep(self.delay)
        # special event edge case
        if is_present(reward):
            instas = self.image_dict["edge cases insta monkey.png"]
            insta_g = self.image_dict["edge cases insta monkey green.png"]
            insta_b = self.image_dict["edge cases insta monkey blue.png"]
            insta_p = self.image_dict["edge cases insta monkey purple.png"]
            insta_y = self.image_dict["edge cases insta monkey yellow.png"]
            cont = self.image_dict["edge cases cont.png"]
            back = self.image_dict["edge cases back.png"]
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
            self.wait_and_check_level(command)
        elif type(command) == tuple:
            if type(command[0]) == str and type(command[1]) == str:
                self.open_track(*command)
            elif type(command[0]) == str and type(command[1]) == tuple:
                self.place(command[0], command[1], delay=self.delay)
            elif type(command[0]) == int and type(command[1]) == tuple:
                self.wait_to_upgrade(*command, delay=self.delay)

    def play(self, parameters):
        log('\n' + str(parameters[0]))
        self.do_command(parameters[0])  # should start the track
        log('\n' + str(parameters[1]))
        self.do_command(parameters[1])  # should place the first tower
        log('\nStart (hit space twice)')
        if parameters[0][2] == "apopalypse":
            hitkeys(' ', self.delay)
        else:
            hitkeys('  ', self.delay)
        for command in parameters[2:]:
            log('\n' + str(command))
            self.do_command(command)
        log('\n' + 'Waiting for track to finish')
        self.wait_to_finish()


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def static_click_and_confirm(image, confirm_images, threshold=4):
    # function to click an image on screen
    # makes sure the image is not moving when clicked
    # will continue to click image until confirmation image is seen
    if type(confirm_images) != list:
        confirm_images = [confirm_images]
    while True:
        prev_spot = (0, -9000)
        spot = (-9000,  0)
        while (spot[0]-prev_spot[0])**2 + (spot[1]-prev_spot[1])**2 > threshold:
            location = pyautogui.locateOnScreen(image, confidence=0.85)
            if location is not None:
                coords = pyautogui.center(location)
                prev_spot = spot
                spot = coords
            if any_present(confirm_images):
                break
        if any_present(confirm_images):
            break
        pyautogui.click(*spot)


def is_present(image):
    # function which determines if a certain image is present
    spot = pyautogui.locateOnScreen(image, confidence=0.85)
    return spot is not None


def any_present(images):
    # function which determines if a certain image is present
    for image in images:
        if is_present(image):
            return True
    return False


def wait_to_see(image):
    # function to pause execution until a particular image appears
    while not is_present(image):
        pass


def click_image(image, delay=0.):
    # function to click an image on screen
    # returns false if image is not on screen
    # returns true if image is successfully clicked
    # will delay by given amount only if button found
    spot = pyautogui.locateOnScreen(image, confidence=0.85)
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


waiting = False
log_txt = ""


def log_path():
    # get path to log file
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        # for log file we want to move up one directory to avoid immediate deletion upon program exit
        base_path = sys._MEIPASS
        base_path = os.path.dirname(base_path)
    except Exception:
        base_path = os.path.abspath(".")
        base_path = os.path.join(base_path, "data\\")

    return os.path.join(base_path, "log.txt")


def log(txt):
    # function which handles logfile output
    global log_txt
    log_txt += txt
    file = open(log_path(), 'w')
    file.write(log_txt)
    file.close()


class ChooseOption:

    def __init__(self, title, caption, options):
        self.choice = None  # selected option
        goal_ratio = 2  # button width to height ratio to aim for
        button_num = 1 + len(options)
        self.pos_finder = RatioFit(pyautogui.size(), 19 / 11, 0)  # initialize position finder
        self.root = tkinter.Tk()
        self.root.title(title)
        frame = tkinter.Frame(self.root)
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        frame.grid(row=0, column=0, sticky="news")
        columns = math.ceil(math.sqrt(goal_ratio*button_num))
        rows = math.ceil(button_num//columns)
        tkinter.Label(frame, text=caption, borderwidth=10).grid(row=0, column=0, columnspan=columns)
        for f in range(len(options)):
            button = tkinter.Button(frame, text=options[f], borderwidth=2,
                                    padx=5, pady=5, command=lambda x=f: self.choose(x))
            button.grid(row=1 + f//columns, column=f%columns, padx=5, pady=5)
        button = tkinter.Button(frame, text="print mouse position", borderwidth=2,
                                padx=5, pady=5, command=self.print_pos)
        button.grid(row=1 + len(options)//columns, column=len(options)%columns, padx=5, pady=5)
        frame.columnconfigure(tuple(range(columns)), weight=1)
        frame.rowconfigure(tuple(range(rows)), weight=1)

    def choose(self, choice):
        self.choice = choice
        self.root.destroy()

    def get_choice(self):
        return self.choice

    def print_pos(self):
        time.sleep(2)
        print(self.pos_finder.revert_pos(pyautogui.position()))
        time.sleep(2)
        print(self.pos_finder.revert_pos(pyautogui.position()))
        time.sleep(2)
        print(self.pos_finder.revert_pos(pyautogui.position()))
        time.sleep(2)
        print(self.pos_finder.revert_pos(pyautogui.position()))
        time.sleep(2)
        print(self.pos_finder.revert_pos(pyautogui.position()))

    def show(self):
        self.root.mainloop()


def main():
    global waiting
    # to get out, move mouse to the corner of the screen to trigger the fail safe
    delay = 0.3
    screen = RatioFit(pyautogui.size(), 19/11, delay)
    # import menu options
    file = open(resource_path("data\\tas.txt"))
    raw_data = file.read()
    file.close()
    option_names = []
    plays = []
    for datum in raw_data.split("\n\n"):
        data = datum.split('\n')
        option_names.append(eval(data[0]))
        plays.append(tuple(eval(d) for d in data[1:]))
    # print log file path
    print('Log file located at:')
    print(log_path())
    # get track choice
    chooser = ChooseOption('BTD6 bot ready', 'Choose which map to play repeatedly', option_names)
    chooser.show()
    choice = chooser.get_choice()
    del chooser
    # start main loop
    mainloop = True
    while mainloop:
        try:
            screen.play(plays[choice])
        except Exception as e:
            log('\n' + repr(e))
            raise


if __name__ == "__main__":
    main()
