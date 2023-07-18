from player import *
from menu import *


def main():
    # to get out, move mouse to the corner of the screen to trigger the failsafe
    screen = RatioFit()
    # manage log files
    path = os.path.join(data_dir(), "log")
    for file in sorted(os.listdir(path)):
        file_s = open(os.path.join(path, file))
        try:
            content = file_s.read()
        except UnicodeError:
            content = True
        file_s.close()
        space_dot = (file.rfind(" "), file.rfind("."))
        if space_dot[0] != -1 and space_dot[1] != -1:
            try:
                file_time = time.mktime(time.strptime(file[space_dot[0]+1: space_dot[1]], "%Y-%m-%d-%H-%M-%S"))
            except ValueError:
                continue
            if time.time() - file_time > 5*24*60*60 or not content:
                # delete after five days or if ile empty
                os.remove(os.path.join(path, file))
    create_log_file()
    # get version
    file = open(os.path.join(data_dir(), "version.txt"))
    version = file.read()
    file.close()
    # open menu
    log(f"Opening GUI for BloonsPlayer version {version}")
    chooser = ChooseOption('BloonsPlayer v' + version, screen)
    chooser.show()


if __name__ == "__main__":
    main()
