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
    plays = []
    base_path = resource_path("data\\tas\\")
    for tas in os.listdir(base_path):
        option_names.append(tas[:tas.find('.')])
        file = open(os.path.join(base_path, tas))
        plays.append(file.read().split('\n'))
        file.close()
    # print log file path
    print('Log file located at:')
    print(log_file())
    # get track choice
    chooser = ChooseOption('BTD6 bot ready', 'Choose which map to play repeatedly', option_names, screen)
    chooser.show()
    choice = chooser.get_choice()
    # start main loop
    mainloop = True
    while mainloop:
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
