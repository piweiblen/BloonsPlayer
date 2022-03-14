from player import fetch_dict, save_dict, parse_args, hit_keys
import threading
import pyautogui
import tkinter.font
import tkinter.ttk
import tkinter
import time


class ChooseOption:

    def __init__(self, title, options, scripts, pos_finder):
        self.options = options
        self.scripts = scripts
        self.pos_finder = pos_finder  # RatioFit class
        self.prefs = fetch_dict("preferences")
        self.difficulties = fetch_dict("map difficulties")
        self.choices = self.prefs["choices"]
        self.filters = dict()
        self.run = False
        # create root
        self.root = tkinter.Tk()
        self.root.title(title)
        self.root.geometry("700x500")
        # set up frame
        frame = tkinter.Frame(self.root)
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        frame.grid(row=0, column=0, sticky="news")
        frame.columnconfigure(tuple(range(3)), weight=1)
        frame.rowconfigure(tuple(range(10)), weight=1)
        # set up list boxes
        self.left_label = tkinter.Label(frame, text="All TAS scripts", borderwidth=10)
        self.left_label.grid(row=0, column=0)
        self.right_label = tkinter.Label(frame, text="Scripts to run", borderwidth=10)
        self.right_label.grid(row=0, column=2)
        self.opts_var = tkinter.StringVar(value=self.options)
        self.option_listbox = tkinter.Listbox(frame, listvariable=self.opts_var, selectmode="extended")
        self.option_listbox.grid(row=1, column=0, rowspan=8, sticky="news")
        self.choice_var = tkinter.StringVar(value=self.prefs["choices"])
        self.choice_listbox = tkinter.Listbox(frame, listvariable=self.choice_var, selectmode="extended")
        self.choice_listbox.grid(row=1, column=2, rowspan=8, sticky="news")
        big_font = tkinter.font.Font(size=30)
        self.pixel = tkinter.PhotoImage(width=1, height=1)
        kwargs = {"font": big_font, "image": self.pixel, "width": 40, "height": 40, "compound": "center"}
        right_button = tkinter.Button(frame, text="⏵", command=self.move_right, **kwargs)
        right_button.grid(row=3, column=1)
        left_button = tkinter.Button(frame, text="⏴", command=self.move_left, **kwargs)
        left_button.grid(row=4, column=1)
        up_button = tkinter.Button(frame, text="⏶", command=self.move_up, **kwargs)
        up_button.grid(row=5, column=1)
        down_button = tkinter.Button(frame, text="⏷", command=self.move_down, **kwargs)
        down_button.grid(row=6, column=1)
        go_button = tkinter.Button(frame, text="GO", command=self.go, padx=5, pady=5)
        go_button.grid(row=9, column=2, padx=5, pady=5)
        # create mouse position utility
        self.print_button = tkinter.Button(frame, text="print mouse position", command=self.position_info,
                                           padx=5, pady=5)
        self.print_button.grid(row=9, column=0, padx=5, pady=5)
        self.toggle_pos = False
        # create menu bars
        self.screen_shot = tkinter.BooleanVar(self.root, self.prefs['screenshot'])
        self.log_times = tkinter.BooleanVar(self.root, self.prefs['log times'])
        self.menu_bar = tkinter.Menu(self.root)
        file_menu = tkinter.Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="Exit", command=self.quit)
        filter_menu = tkinter.Menu(self.menu_bar, tearoff=0)
        self.create_filter_menu(filter_menu, 0, "Map Difficulty",
                                ["beginner", "intermediate", "advanced", "expert"], self.is_difficulty)
        self.create_filter_menu(filter_menu, 1, "Game Difficulty",
                                ["easy", "medium", "hard"], self.is_game)
        self.create_filter_menu(filter_menu, 2, "Game Mode",
                                ["standard", "sandbox", "other"], self.is_mode)
        option_menu = tkinter.Menu(self.menu_bar, tearoff=0)
        option_menu.add_checkbutton(label="Take Screenshot On Failure", onvalue=1, offvalue=0,
                                    variable=self.screen_shot, command=self.update_prefs)
        option_menu.add_checkbutton(label="Log Round Times", onvalue=1, offvalue=0,
                                    variable=self.log_times, command=self.update_prefs)
        # build menu bar structure
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        self.menu_bar.add_cascade(label="Filter", menu=filter_menu)
        self.menu_bar.add_cascade(label="Options", menu=option_menu)
        self.root.config(menu=self.menu_bar)

    def update_prefs(self):
        self.prefs['screenshot'] = self.screen_shot.get()
        self.prefs['log times'] = self.log_times.get()
        self.prefs['choices'] = self.choices
        save_dict('preferences', self.prefs)
        self.pos_finder.update_prefs()

    def update_listboxes(self):
        self.opts_var.set(value=self.options)

    def move_right(self):
        selected_left = [self.option_listbox.get(f) for f in self.option_listbox.curselection()]
        self.choices += selected_left
        self.update_prefs()
        self.choice_var.set(value=self.choices)

    def move_left(self):
        selected_right = self.choice_listbox.curselection()
        self.choices = [self.choices[f] for f in range(len(self.choices)) if f not in selected_right]
        self.choice_var.set(value=self.choices)
        self.update_prefs()
        self.choice_listbox.select_clear(0, len(self.choices))

    def move_up(self):
        selected_right = self.choice_listbox.curselection()
        if 0 in selected_right:
            return None
        self.choice_listbox.select_clear(0, len(self.choices))
        new_choices = [self.choices[f] for f in range(len(self.choices)) if f not in selected_right]
        for ind in selected_right:
            new_choices.insert(ind-1, self.choices[ind])
            self.choice_listbox.select_set(ind-1)
        self.choices = new_choices
        self.choice_var.set(value=self.choices)
        self.update_prefs()

    def move_down(self):
        selected_right = self.choice_listbox.curselection()
        if len(self.choices)-1 in selected_right:
            return None
        self.choice_listbox.select_clear(0, len(self.choices))
        new_choices = [self.choices[f] for f in range(len(self.choices)) if f not in selected_right]
        for ind in selected_right:
            new_choices.insert(ind+1, self.choices[ind])
            self.choice_listbox.select_set(ind+1)
        self.choices = new_choices
        self.choice_var.set(value=self.choices)
        self.update_prefs()

    def perform_filtering(self):
        self.option_listbox.select_clear(0, len(self.opts_var.get()))
        if self.filters:
            self.left_label["text"] = "Filtered TAS Scripts"
        else:
            self.left_label["text"] = "All TAS Scripts"
        new_opts = []
        for option in self.options:
            passes = True
            for func in self.filters:
                if not any(func(parameter, option) for parameter in self.filters[func]):
                    passes = False
                    break
            if passes:
                new_opts.append(option)
        self.opts_var.set(new_opts)

    def create_filter_menu(self, parent, index, name, opts, det):
        # create a filtering menu from a filter name, options, and determining function
        menu = tkinter.Menu(parent, tearoff=0)
        if name in self.prefs["filters"]:
            bools = [tkinter.BooleanVar(self.root, self.prefs["filters"][name][f]) for f in range(len(opts)+1)]
        else:
            bools = [tkinter.BooleanVar(self.root, True) for f in range(len(opts)+1)]

        # generate menu and commands
        def command():
            hit_keys(['alt', 'f', 'enter'] + index*["down"] + ['right'], 0)
            self.set_filter(name, opts, bools, det)

        def clear():
            hit_keys(['alt', 'f', 'enter'] + index*["down"] + ['right'], 0)
            for b in bools:
                b.set(False)
            self.set_filter(name, opts, bools, det)

        menu.add_checkbutton(label="all", onvalue=1, offvalue=0, variable=bools[0], command=command)
        for f in range(len(opts)):
            menu.add_checkbutton(label=opts[f], onvalue=1, offvalue=0, variable=bools[f+1], command=command)
        menu.add_command(label="clear", command=clear)
        self.set_filter(name, opts, bools, det)
        parent.add_cascade(label=name, menu=menu)

    def set_filter(self, name, opts, bools, det):
        # perform actual filtering
        if bools[0].get():
            if det in self.filters:
                del self.filters[det]
                self.perform_filtering()
            if not any(b.get() for b in bools[1:]):
                # if the rest are false, set all to true
                for b in bools:
                    b.set(True)
        else:
            self.filters[det] = [opts[f] for f in range(len(opts)) if bools[f+1].get()]
            self.perform_filtering()
        # update and save preferences
        if all(b.get() for b in bools):
            if name in self.prefs["filters"]:
                del self.prefs["filters"][name]
        else:
            self.prefs["filters"][name] = tuple(b.get() for b in bools)
        self.update_prefs()

    def is_difficulty(self, difficulty, option):
        open_args = parse_args(self.scripts[option][0], "open")
        if not open_args:
            return False
        return difficulty == self.difficulties[open_args[0]]

    def is_game(self, difficulty, option):
        open_args = parse_args(self.scripts[option][0], "open")
        if not open_args:
            return False
        return difficulty == open_args[1]

    def is_mode(self, mode, option):
        open_args = parse_args(self.scripts[option][0], "open")
        if not open_args:
            return False
        if mode == open_args[2]:
            return True
        if mode == "other" and open_args[2] not in ["standard", "sandbox"]:
            return True
        return False

    def quit(self):
        self.toggle_pos = False
        self.root.destroy()

    def go(self):
        self.run = True
        self.quit()

    def get_choice(self):
        return self.choices

    def display_pos(self):
        previous = ""
        current = ""
        counter = 0
        while self.toggle_pos and 'normal' == self.root.state():
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
