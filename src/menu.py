from player import fetch_dict, save_dict
import threading
import pyautogui
import tkinter
import math
import time


class ChooseOption:

    def __init__(self, title, caption, options, pos_finder):
        self.choice = None  # selected option
        goal_ratio = 1.3  # button width to height ratio to aim for
        button_num = 1 + len(options)
        self.pos_finder = pos_finder  # RatioFit class
        self.prefs = fetch_dict("preferences")
        # create root
        self.root = tkinter.Tk()
        self.root.title(title)
        # create menu bar
        menu_bar = tkinter.Menu(self.root)
        file_menu = tkinter.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Exit", command=self.root.quit)
        menu_bar.add_cascade(label="File", menu=file_menu)
        option_menu = tkinter.Menu(menu_bar, tearoff=0)
        self.screen_shot = tkinter.BooleanVar(self.root, self.prefs['screenshot'])
        option_menu.add_checkbutton(label="Take Screenshot On Failure", onvalue=1, offvalue=0,
                                    variable=self.screen_shot, command=self.set_prefs)
        self.log_times = tkinter.BooleanVar(self.root, self.prefs['log times'])
        option_menu.add_checkbutton(label="Log Round Times", onvalue=1, offvalue=0,
                                    variable=self.log_times, command=self.set_prefs)
        menu_bar.add_cascade(label="Options", menu=option_menu)
        self.root.config(menu=menu_bar)
        # create buttons
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
        self.print_button = tkinter.Button(frame, text="print mouse position", borderwidth=2,
                                           padx=5, pady=5, command=self.position_info)
        self.print_button.grid(row=1 + len(options)//columns, column=len(options)%columns, padx=5, pady=5)
        self.toggle_pos = False
        frame.columnconfigure(tuple(range(columns)), weight=1)
        frame.rowconfigure(tuple(range(rows)), weight=1)

    def set_prefs(self):
        self.prefs['screenshot'] = self.screen_shot.get()
        self.prefs['log times'] = self.log_times.get()
        save_dict('preferences', self.prefs)
        self.pos_finder.update_prefs()

    def choose(self, choice):
        self.toggle_pos = False
        time.sleep(0.06)
        self.choice = choice
        self.root.destroy()

    def get_choice(self):
        return self.choice

    def display_pos(self):
        previous = ""
        current = ""
        counter = 0
        while self.toggle_pos:
            time.sleep(0.03)
            position = self.pos_finder.revert_pos(pyautogui.position())
            previous = current
            current = "({:.5f}, {:.5f})".format(*position)
            self.print_button['text'] = current
            if previous == current:
                counter += 1
            else:
                counter = 0
            if counter == 60 and 0 <= position[0] <= 1 and 0 <= position[1] <= 1:
                print(current)
                self.root.clipboard_clear()
                self.root.clipboard_append(current)
        self.print_button['text'] = "Display mouse position"

    def position_info(self):
        self.toggle_pos = not self.toggle_pos
        if self.toggle_pos:
            newt = threading.Thread(target=self.display_pos, daemon=True)
            newt.start()

    def show(self):
        self.root.mainloop()
