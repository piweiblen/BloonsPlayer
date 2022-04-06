from player import *
import threading
import pyautogui
import tkinter
import tkinter.font
from tkinter import filedialog
from tkinter import messagebox
import time
import os


class ChooseOption:

    def __init__(self, title, pos_finder):
        self.options = []
        self.scripts = {}
        self.pos_finder = pos_finder  # RatioFit class
        self.prefs = fetch_dict("preferences")
        self.difficulties = fetch_dict("map difficulties")
        self.game_modes = fetch_dict("game modes")
        self.choices = self.prefs["choices"]
        if not self.prefs['steam path']:
            self.prefs['steam path'] = steam_path()
        self.filters = dict()
        self.run = False
        # create root
        self.root = tkinter.Tk()
        self.root.title(title)
        self.root.geometry("700x500")
        # set up frame
        self.frame = tkinter.Frame(self.root)
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.frame.grid(row=0, column=0, sticky="news")
        self.frame.columnconfigure(tuple(range(3)), weight=1)
        self.frame.rowconfigure(tuple(range(11)), weight=1)

        # set up list boxes
        self.left_label = tkinter.Label(self.frame, text="All TAS scripts", borderwidth=10)
        self.left_label.grid(row=0, column=0)
        self.right_label = tkinter.Label(self.frame, text="Scripts to run", borderwidth=10)
        self.right_label.grid(row=0, column=2)
        self.opts_var = tkinter.StringVar(value=self.options)
        self.option_listbox = tkinter.Listbox(self.frame, listvariable=self.opts_var, selectmode="extended")
        self.option_listbox.grid(row=1, column=0, rowspan=8, sticky="news")
        self.choice_var = tkinter.StringVar(value=self.prefs["choices"])
        self.choice_listbox = tkinter.Listbox(self.frame, listvariable=self.choice_var, selectmode="extended")
        self.choice_listbox.grid(row=1, column=2, rowspan=8, sticky="news")
        big_font = tkinter.font.Font(size=30)
        self.pixel = tkinter.PhotoImage(width=1, height=1)
        kwargs = {"font": big_font, "image": self.pixel, "width": 40, "height": 40, "compound": "center"}
        # listbox manip buttons
        self.right_button = tkinter.Button(self.frame, text="⏵", command=self.move_right, **kwargs)
        self.right_button.grid(row=3, column=1)
        self.left_button = tkinter.Button(self.frame, text="⏴", command=self.move_left, **kwargs)
        self.left_button.grid(row=4, column=1)
        self.up_button = tkinter.Button(self.frame, text="⏶", command=self.move_up, **kwargs)
        self.up_button.grid(row=5, column=1)
        self.down_button = tkinter.Button(self.frame, text="⏷", command=self.move_down, **kwargs)
        self.down_button.grid(row=6, column=1)
        # go button
        self.go_button = tkinter.Button(self.frame, text="GO", command=self.go, padx=5, pady=5)
        self.go_button.grid(row=9, column=2, padx=5, pady=5)
        # create mouse position utility
        self.print_button = tkinter.Button(self.frame, text="print mouse position", command=self.position_info,
                                           padx=5, pady=5)
        self.print_button.grid(row=9, column=0, padx=5, pady=5)
        self.toggle_pos = False
        # launch btd6 button
        self.launch_button = tkinter.Button(self.frame, text="launch btd6", command=self.launch, padx=5, pady=5)
        self.launch_button.grid(row=10, column=0, padx=5, pady=5)
        # collection event button
        self.easter_button = tkinter.Button(self.frame, text="egg mode", command=self.egg_mode, padx=5, pady=5)
        self.easter_button.grid(row=10, column=2, padx=5, pady=5)

        # create menu bars
        self.screen_shot = tkinter.BooleanVar(self.root, self.prefs['screenshot'])
        self.log_times = tkinter.BooleanVar(self.root, self.prefs['log times'])
        self.crash_p = tkinter.BooleanVar(self.root, self.prefs['crash protection'])
        self.menu_bar = tkinter.Menu(self.root)
        # file menu
        file_menu = tkinter.Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="Refresh Scripts", command=self.get_options)
        file_menu.add_command(label="Exit", command=self.quit)
        # filter menu
        filter_menu = tkinter.Menu(self.menu_bar, tearoff=0)
        self.filter_bools = {}
        self.create_filter_menu(filter_menu, "Map Difficulty",
                                ["beginner", "intermediate", "advanced", "expert"], self.is_difficulty)
        self.create_filter_menu(filter_menu, "Map Name",
                                [m for m in self.difficulties], self.is_map)
        self.create_filter_menu(filter_menu, "Game Difficulty",
                                ["easy", "medium", "hard"], self.is_game)
        self.create_filter_menu(filter_menu, "Game Mode",
                                [m for m in self.game_modes], self.is_mode)
        filter_menu.add_command(label="Reset All", command=self.clear_all_filters)
        # options menu
        option_menu = tkinter.Menu(self.menu_bar, tearoff=0)
        option_menu.add_checkbutton(label="Take Screenshot On Failure", onvalue=1, offvalue=0,
                                    variable=self.screen_shot, command=self.update_prefs)
        option_menu.add_checkbutton(label="Log Round Times", onvalue=1, offvalue=0,
                                    variable=self.log_times, command=self.update_prefs)
        option_menu.add_checkbutton(label="Restart Game On Crash", onvalue=1, offvalue=0,
                                    variable=self.crash_p, command=self.crash_p_toggle)
        # style menu
        style_menu = tkinter.Menu(self.menu_bar, tearoff=0)
        self.styles = {"light": ("#f0f0f0", "#ffffff", "#000000", "#0078d7"),
                       "dark": ("#404040", "#202020", "#ffffff", "#497ba1"),
                       "amoled": ("#000000", "#101010", "#f0f0f0", "#c02020")}
        self.create_single_select_menu(style_menu, self.styles.keys(), self.set_style, self.prefs['theme'])
        self.set_style(self.prefs['theme'])
        # build menu bar structure
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        self.menu_bar.add_cascade(label="Filter", menu=filter_menu)
        self.menu_bar.add_cascade(label="Options", menu=option_menu)
        self.menu_bar.add_cascade(label="Themes", menu=style_menu)
        self.root.config(menu=self.menu_bar)
        self.get_options()
        self.update_prefs()

    def set_style(self, name):
        back, more_back, front, accent = self.styles[name]
        self.prefs['theme'] = name
        self.update_prefs()
        standard = {"bg": back, "fg": front}
        button = {"bg": back, "fg": front, "activebackground": more_back, "activeforeground": front}
        box = {"bg": more_back, "fg": front, "selectbackground": accent, "selectforeground": more_back}
        menu_style = {"bd": 0, "bg": back, "fg": front, "activebackground": accent,
                      "activeforeground": more_back, "selectcolor": front}
        self.frame.config(bg=back)
        self.right_label.config(**standard)
        self.left_label.config(**standard)
        self.right_button.config(**button)
        self.left_button.config(**button)
        self.up_button.config(**button)
        self.down_button.config(**button)
        self.print_button.config(**button)
        self.go_button.config(**button)
        self.launch_button.config(**button)
        self.easter_button.config(**button)
        self.choice_listbox.config(**box)
        self.option_listbox.config(**box)

        def recurse_set_menu(menu):
            menu.config(**menu_style)
            for c in menu.children:
                child = menu.nametowidget(c)
                recurse_set_menu(child)

        recurse_set_menu(self.menu_bar)

    def create_single_select_menu(self, parent, options, func, initial):
        options = sorted(options)
        bools = [tkinter.BooleanVar(self.root, False) for f in range(len(options))]
        bools[options.index(initial)].set(True)
        for f in range(len(options)):
            def command(index=f):
                for g in range(len(options)):
                    bools[g].set(False)
                bools[index].set(True)
                func(options[index])
            parent.add_checkbutton(label=options[f], onvalue=1, offvalue=0, variable=bools[f], command=command)

    def get_options(self):
        self.options = []
        self.scripts = {}
        base_path = os.path.join(data_dir(), "tas")
        for tas in os.listdir(base_path):
            if not tas.endswith(".txt"):
                continue
            self.options.append(tas[:-4])
            file = open(os.path.join(base_path, tas))
            self.scripts[tas[:-4]] = tuple(file.read().split('\n'))
            file.close()
        self.perform_filtering()

    def steam_prompt(self):
        cant = "BloonsPlayer cannot find steam on your system"
        if messagebox.askyesno(cant, cant+"\nWould you like to browse your files for steam?"):
            self.prefs['steam path'] = filedialog.askopenfilename(initialdir="/",
                                                         title="Select steam executable",
                                                         filetypes=(("EXE (*.exe)", "*.exe"),))
        self.update_prefs()

    def crash_p_toggle(self):
        if self.crash_p.get():
            if not self.prefs['steam path']:
                self.steam_prompt()
                self.crash_p.set(bool(self.prefs['steam path']))
        self.update_prefs()

    def update_prefs(self):
        self.prefs['screenshot'] = self.screen_shot.get()
        self.prefs['log times'] = self.log_times.get()
        self.prefs['crash protection'] = self.crash_p.get()
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
        # perform actual filtering
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

    def create_filter_menu(self, parent, name, opts, det):
        # create a filtering menu from a filter name, options, and determining function
        index = len(self.filter_bools)
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
        self.filter_bools[name] = bools

    def set_filter(self, name, opts, bools, det):
        # handle a filter change
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
        self.save_filters(name, bools)

    def save_filters(self, name, bools):
        # update and save preferences
        if all(b.get() for b in bools):
            if name in self.prefs["filters"]:
                del self.prefs["filters"][name]
        else:
            self.prefs["filters"][name] = tuple(b.get() for b in bools)
        self.update_prefs()

    def clear_all_filters(self):
        for name in self.filter_bools:
            for b in self.filter_bools[name]:
                b.set(True)
            self.save_filters(name, self.filter_bools[name])
        self.filters = {}
        self.prefs["filters"] = {}
        self.update_prefs()
        self.perform_filtering()

    def is_difficulty(self, difficulty, option):
        open_args = parse_args(self.scripts[option][0], "open")
        if not open_args:
            return False
        return difficulty == self.difficulties[open_args[0]]

    def is_map(self, track, option):
        open_args = parse_args(self.scripts[option][0], "open")
        if not open_args:
            return False
        return track == open_args[0]

    def is_game(self, difficulty, option):
        open_args = parse_args(self.scripts[option][0], "open")
        if not open_args:
            return False
        return difficulty == open_args[1]

    def is_mode(self, mode, option):
        open_args = parse_args(self.scripts[option][0], "open")
        if not open_args:
            return False
        return mode == open_args[2]

    def quit(self):
        self.toggle_pos = False
        self.root.destroy()

    def go(self):
        self.run = True
        if self.prefs['crash protection']:
            self.launch()
        self.quit()

    def launch(self):
        if self.prefs['steam path']:
            self.pos_finder.launch_bloons()
        else:
            self.steam_prompt()

    def egg_mode(self):
        self.pos_finder.egg_mode = True
        self.go()

    def get_choice(self):
        return [self.scripts[c] for c in self.choices]

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
