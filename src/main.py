from player import *
from menu import *
import pyautogui
import os


def main():
    clear_log()
    # to get out, move mouse to the corner of the screen to trigger the failsafe
    screen = RatioFit(pyautogui.size(), 0.3)
    # import menu options
    option_names = []
    plays = {}
    base_path = resource_path("data\\tas\\")
    for tas in os.listdir(base_path):
        if not tas.endswith(".txt"):
            continue
        option_names.append(tas[:-4])
        file = open(os.path.join(base_path, tas))
        plays[tas[:-4]] = tuple(file.read().split('\n'))
        file.close()
    # print log file path
    print('Log file located at:')
    print(log_file())
    # get track choice
    chooser = ChooseOption('BloonsPlayer v0.2.0', option_names, plays, screen)
    chooser.show()
    choices = chooser.get_choice()
    if not choices or not chooser.run:
        print("No selection made")
        return None
    # start main loop
    mainloop = True
    while mainloop:
        for choice in choices:
            try:
                screen.play(plays[choice])
            except Exception as e:
                log('\n' + repr(e))
                if type(e) != BloonsError:
                    raise
            finally:
                screen.kill_threads()


if __name__ == "__main__":
    main()
