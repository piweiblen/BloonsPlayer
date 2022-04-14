from player import *
from menu import *


def main():
    # to get out, move mouse to the corner of the screen to trigger the failsafe
    screen = RatioFit()
    # manage log files
    path = os.path.join(data_dir(), "log")
    new_file = os.path.join(path, "log " + time.strftime("%Y-%m-%d-%H-%M-%S") + ".txt")
    if not os.path.exists(new_file):
        open(new_file, "w").close()
    for file in sorted(os.listdir(path)):
        space_dot = (file.rfind(" "), file.rfind("."))
        if space_dot[0] != -1 and space_dot[1] != -1:
            try:
                file_time = time.mktime(time.strptime(file[space_dot[0]+1: space_dot[1]], "%Y-%m-%d-%H-%M-%S"))
            except ValueError:
                continue
            if time.time() - file_time > 5*24*60*60:  # five days
                os.remove(os.path.join(path, file))
    # get version
    file = open(os.path.join(data_dir(), "version.txt"))
    version = file.read()
    file.close()
    # open menu
    chooser = ChooseOption('BloonsPlayer v' + version, screen)
    chooser.show()


if __name__ == "__main__":
    main()
