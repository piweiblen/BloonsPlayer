import pyautogui
from PIL import Image
import time
import sys
import os


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
        pyautogui.press(self.monkey_dict[monkey])
        pyautogui.moveTo(*self.convert_pos(position))
        time.sleep(delay/2)
        pyautogui.click(*self.convert_pos(position))
        time.sleep(delay/2)

    def upgrade(self, monkey_index, path, delay=0.):
        # upgrade the specified monkey into the specified path
        pyautogui.click(*self.convert_pos(self.monkeys_placed[monkey_index][1]))
        time.sleep(delay/2)
        pyautogui.press(self.upgrade_dict[path])
        time.sleep(delay/2)
        pyautogui.press('esc')

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
            time.sleep(delay/2)
            pyautogui.press(self.upgrade_dict[p])
            time.sleep(delay/2)
        pyautogui.press('esc')

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
            pyautogui.press(' ')
            return True
        return False

    def wait_and_check_level(self, secs):
        # function waits a given amount of time, and regularly check if you've leveled up
        if time_left := shows_up(self.open_image(r"images\edge cases\LEVEL UP.png"), secs):
            wait_until_click(self.open_image(r"images\edge cases\LEVEL UP.png"))
            if shows_up(self.open_image(r"images\edge cases\monkey knowledge.png"), 1):
                click_image(self.open_image(r"images\edge cases\monkey knowledge.png"))
            time.sleep(0.3)
            pyautogui.press(' ')
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
                pyautogui.press('esc')

    def do_command(self, command):
        if type(command) == int:
            time.sleep(command)
        elif type(command) == tuple:
            if type(command[0]) == str and type(command[1]) == str:
                self.open_track(*command)
            elif type(command[0]) == str and type(command[1]) == tuple:
                self.place(command[0], command[1], delay=self.delay)
            elif type(command[0]) == int and type(command[1]) == tuple:
                self.wait_to_upgrade(*command)

    def play(self, parameters):
        self.do_command(parameters[0])  # should start the track
        self.do_command(parameters[1])  # should place the first tower
        pyautogui.write('  ', interval=self.delay)
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
    options = ['monkey meadow (easy)', 'flooded valley (easy)']
    # how to play each menu option
    plays = [(("monkey meadow", "easy"),  # choose map
              ("hero", (0.1, 0.5)),  # place tower
              10,  # delay
              ("sniper", (0.8, 0.43)),
              (1, (2, 2, 1, 2, 1))),  # upgrade tower

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
