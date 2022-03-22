from player import *
from menu import *


def main():
    clear_log()
    # to get out, move mouse to the corner of the screen to trigger the failsafe
    screen = RatioFit()
    # print log file path
    print('Log file located at:')
    print(log_file())
    # get track choice
    chooser = ChooseOption('BloonsPlayer v0.2.1', screen)
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
                screen.play(choice)
            except Exception as e:
                log('\n' + repr(e))
                if type(e) != BloonsError:
                    raise
            finally:
                screen.kill_threads()


if __name__ == "__main__":
    main()
