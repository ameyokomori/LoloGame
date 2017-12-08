"""
CSSE1001 Assignment 3
Semester 1, 2017
"""

import tkinter as tk
from tkinter import messagebox
import random
import winsound
import json

import model
import view
import highscores
from game_regular import RegularGame
# # For alternative game modes
from game_make13 import Make13Game
from game_lucky7 import Lucky7Game
from game_unlimited import UnlimitedGame
from highscores import HighScoreManager

__author__ = "<Wayne>"

__version__ = "1.1.2"


# Once you have created your basic gui (LoloApp), you can delete this class
# and replace it with the following:
# from base import BaseLoloApp
class BaseLoloApp:
    """Base class for a simple Lolo game."""

    def __init__(self, master, game=None, grid_view=None):
        """Constructor

        Parameters:
            master (tk.Tk|tk.Frame): The parent widget.
            game (model.AbstractGame): The game to play. Defaults to a
                                       game_regular.RegularGame.
            grid_view (view.GridView): The view to use for the game. Optional.

        Raises:
            ValueError: If grid_view is supplied, but game is not.
        """
        self._master = master

        # Game
        if game is None:
            game = RegularGame(types=3)

        self._game = game

        # Grid View
        if grid_view is None:
            if game is None:
                raise ValueError("A grid view cannot be given without a game.")
            grid_view = view.GridView(master, self._game.grid.size())

        self._grid_view = grid_view
        self._grid_view.pack()

        self._grid_view.draw(self._game.grid, self._game.find_connections())

        # Events
        self.bind_events()

    def bind_events(self):
        """Binds relevant events."""
        self._grid_view.on('select', self.activate)
        self._game.on('game_over', self.game_over)
        self._game.on('score', self.score)

    def create_animation(self, generator, delay=200, func=None, callback=None):
        """Creates a function which loops through a generator using the tkinter
        after method to allow for animations to occur

        Parameters:
            generator (generator): The generator yielding animation steps.
            delay (int): The delay (in milliseconds) between steps.
            func (function): The function to call after each step.
            callback (function): The function to call after all steps.

        Return:
            (function): The animation runner function.
        """

        def runner():
            try:
                value = next(generator)
                self._master.after(delay, runner)
                if func is not None:
                    func()
            except StopIteration:
                if callback is not None:
                    callback()

        return runner

    def activate(self, position):
        """Attempts to activate the tile at the given position.

        Parameters:
            position (tuple<int, int>): Row-column position of the tile.

        Raises:
            IndexError: If position cannot be activated.
        """
        # Magic. Do not touch.
        if position is None:
            return

        if self._game.is_resolving():
            return

        if position in self._game.grid:

            if not self._game.can_activate(position):
                hell = IndexError("Cannot activate position {}".format(position))
                raise hell  # he he

            def finish_move():
                self._grid_view.draw(self._game.grid,
                                     self._game.find_connections())

            def draw_grid():
                self._grid_view.draw(self._game.grid)

            animation = self.create_animation(self._game.activate(position),
                                              func=draw_grid,
                                              callback=finish_move)
            animation()

    def remove(self, *positions):
        """Attempts to remove the tiles at the given positions.

        Parameters:
            *positions (tuple<int, int>): Row-column position of the tile.

        Raises:
            IndexError: If position cannot be activated.
        """
        if len(positions) is None:
            return

        if self._game.is_resolving():
            return

        def finish_move():
            self._grid_view.draw(self._game.grid,
                                 self._game.find_connections())

        def draw_grid():
            self._grid_view.draw(self._game.grid)

        animation = self.create_animation(self._game.remove(*positions),
                                          func=draw_grid,
                                          callback=finish_move)
        animation()

    def reset(self):
        """Resets the game."""
        raise NotImplementedError("Abstract method")

    def game_over(self):
        """Handles the game ending."""
        raise NotImplementedError("Abstract method")  # no mercy for stooges

    def score(self, score):
        """Handles change in score.

        Parameters:
            score (int): The new score.
        """

        # Normally, this should raise the following error:
        # raise NotImplementedError("Abstract method")
        # But so that the game can work prior to this method being implemented,
        # we'll just print some information.
        # Sometimes I believe Python ignores all my comments :(
        print("Score is now {}.".format(score))
        print("Don't forget to override the score method!")

        # Note: # score can also be retrieved through self._game.get_score()


# Define your classes here
class LoloApp(BaseLoloApp):
    """Class for a Lolo game."""
    def __init__(self, master, game=None, grid_view=None, playername='None'):
        """Constructor

        Parameters:
            master (tk.Tk|tk.Frame): The parent widget.
            game (model.AbstractGame): The game to play. Defaults to a
                                        game_regular.RegularGame.
            grid_view (view.GridView): The view to use for the game. Optional.

        Raises:
            ValueError: If grid_view is supplied, but game is not.
        """
        self._master = master
        self._player_name = playername
        self._game = game
        self._lightning_count = 2
        self._grid_view = grid_view
        self._file = playername + '_' + self._game.get_name() + '_save.json'
        self._savegame = SaveGame(self._file, game.get_name(), self._lightning_count)
        self._loadgame = {}

        self._logo_frame = tk.Frame(self._master)
        self._logo_frame.pack(side=tk.TOP, fill=tk.BOTH)

        self._statusBar = tk.Frame(self._master)
        self._statusBar.pack(side=tk.TOP, fill=tk.BOTH, padx=10)

        super().__init__(self._master, self._game, self._grid_view)

        self._master.title('Lolo :: ' + self._game.get_name() + ' Game')

        self._menubar = tk.Menu(self._master)
        self._master.config(menu=self._menubar)

        filemenu = tk.Menu(self._menubar, tearoff=0)
        self._menubar.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(label="New Game", command=self.reset)
        filemenu.add_command(label="Save", command=lambda: self._savegame.record(self._game.get_score(), self._game, self._player_name, self._lightning_count))
        filemenu.add_command(label="Load", command=self.loadgame)
        filemenu.add_command(label="Exit", command=quit)
        self.filename = None

        self._logo = LoloLogo(self._logo_frame)
        self._sb = StatusBar(self._statusBar, self._game, self._player_name)

        self._sb.set_game(self._game.get_name())
        self._sb.set_score(self._game.get_score())

        self._lightning_frame = tk.Frame(self._master)
        self._lightning_frame.pack(side=tk.BOTTOM)

        self._lightningbt = tk.Button(self._lightning_frame, text="Lightning ({})".format(self._lightning_count), command=self.lightning)
        self._lightningbt.pack(side=tk.BOTTOM)
        self._lightning_on = False

        self._round_count = 0

        self._master.bind("<KeyPress>", self.keyboardevent)

        self.reset()

    def bind_events(self):
        """Binds relevant events."""
        self._grid_view.on('select', self.activate)
        self._game.on('game_over', self.game_over)

    def loadgame(self):
        """Load saved game from json file."""
        try:
            self._loadgame = self._savegame.load()
        except json.JSONDecodeError:
            messagebox.showinfo(title="Load", message="Load Failed")
        if self._loadgame == {}:
            messagebox.showinfo(title="Load", message="Load Failed")
        else:
            self._game = RegularGame.deserialize(self._loadgame["grid"])
            self._game.set_score(self._loadgame["score"])
            self._sb.set_score(self._loadgame["score"])
            self._grid_view.draw(self._game.grid, self._game.find_connections())
            self._lightning_count = self._loadgame["lighting"]
            if self._lightning_count <= 0:
                self._lightningbt.config(text="Lightning ({})".format(self._lightning_count), state=tk.DISABLED)
                self._lightning_on = False
            else:
                self._lightningbt.config(text="Lightning ({})".format(self._lightning_count), state=tk.NORMAL)
            messagebox.showinfo(title="Load", message="Load Successful")

    def keyboardevent(self, event):
        """
        Bind keyboard event
        Press Control+n to start a new game, press Control+l to activate lighting function.

        Parameters:
            event (event): The keyboard event.
                event.state == 4 is <Control>
        """
        if event.state == 4 and event.keysym == "n":
            self.reset()
        elif event.state == 4 and event.keysym == "l":
            self.lightning()

    def reset(self):
        """Reset the game (start a new game)."""
        self._game.reset()
        self._sb.set_game(self._game.get_name())
        self._sb.set_score(self._game.get_score())
        self._grid_view.draw(self._game.grid, self._game.find_connections())
        self._lightning_count = 2
        self._lightningbt.config(text="Lightning ({})".format(self._lightning_count), state=tk.NORMAL)

    def activate(self, position):
        """Attempts to activate the tile at the given position.

        Parameters:
            position (tuple<int, int>): Row-column position of the tile.
        """
        try:
            # Check whether lighting function is activated
            if self._lightning_on:
                self.remove(position)
                self._lightning_on = False
                if self._lightning_count == 0:
                    self._lightningbt.config(text="Lightning ({})".format(self._lightning_count), state=tk.DISABLED)
                else:
                    self._lightningbt.config(text="Lightning ({})".format(self._lightning_count), state=tk.NORMAL)
            else:
                super().activate(position)
                self._sb.set_score(self._game.get_score())
                self._round_count += 1
                self.lightning_gain()

        except IndexError:
            messagebox.showinfo(title="Invalid Activation", message="Cannot activate position {}".format(position))

    def game_over(self):
        """Handles the game ending."""
        self.save_record()
        self._lightningbt.config(text="Lightning ({})".format(self._lightning_count), state=tk.DISABLED)
        self._lightning_on = False
        messagebox.showinfo(title="Game Over", message="Your final score is {}".format(self._game.get_score()))

    def lightning(self):
        """Define the lighting function."""
        if self._lightning_count > 0:
            self._lightningbt.config(text="Lightning On".format(self._lightning_count), state=tk.DISABLED)
            self._lightning_on = True
            self._lightning_count -= 1
            # self.save_record()
        else:
            self._lightningbt.config(text="Lightning ({})".format(self._lightning_count), state=tk.DISABLED)
            self._lightning_on = False

    def lightning_gain(self):
        """When meet some conditions can gain extra lighting chances."""
        if self._round_count % 20 == 0:
            print(self._game.get_score() % 20)
            self._lightning_count += 1
            self._lightningbt.config(text="Lightning ({})".format(self._lightning_count), state=tk.NORMAL)

    def save_record(self):
        """Save game record."""
        record = HighScoreManager()
        record.record(self._game.get_score(), self._game, self._player_name)


class SaveGame(HighScoreManager):
    """Class for game saving"""
    def __init__(self, filename, gamemode, lightning_count):
        """Constructs a game save using the provided json file.

        Parameters:
            filename (str): The name of the json file which stores the game
                        information.
            gamemode (str): The name of the game mode to load game from.
            lightning_count (int): The number of rest lightning function chance

        """
        self._file = filename
        self._gamemode = gamemode
        self._lighting_count = lightning_count
        self._datasave = {}
        self._dataload = {}

    def _load_json(self):
        """Loads the game save json file."""
        try:
            with open(self._file) as file:
                try:
                    data = json.load(file)
                except json.JSONDecodeError:
                    # Failed to decode the json file
                    # Default to empty leaderboard
                    data = {}
        except IOError:
            # Could not locate the json file
            # Default to empty leaderboard
            data = {}

        return data

    def load(self):
        """Loads the game save information from the game save file.
        """
        self._dataload = self._load_json()
        return self._dataload

    def save(self):
        """Saves the information of current game to the file."""
        with open(self._file, "w") as file:
            file.write(json.dumps(self._datasave))
            messagebox.showinfo(title="Save", message="Save Successful")

    def record(self, score, grid, name=None, lighting_count=2):
        """Makes a record of a game save based on the score, grid, name and lightning count.

        Parameters:
            score (int): The current score of the game.
            grid (LoloGrid): A grid to be serialized into the file.
            name (str): The name of the player.
            lighting_count (int): The number of lightning chance.
        """
        self._datasave = {"score": score, "name": str(name), "grid": grid.serialize(), "lighting": lighting_count}
        print(self._datasave)
        self.save()


class StatusBar(tk.Frame):
    """Class for setting the status bar in lolo game."""
    def __init__(self, statusbar, game, playername):
        """Constructor

        Parameters:
            statusbar (th.Tk|tk.Frame): The parent widget.
            game (model.AbstractGame): The game to play. Defaults to a
                                        game_regular.RegularGame.
            playername (string): The name of current player.
        """
        super().__init__()

        self._statusBar = statusbar
        self._game = game
        self._player_name = playername

        self._game_label = tk.Label(self._statusBar, text='Abstract Mode')
        self._game_label.pack(side=tk.LEFT)

        self._score_label = tk.Label(self._statusBar, text='Score: 0')
        self._score_label.pack(side=tk.RIGHT)

        self._name_label = tk.Label(self._statusBar, text='Player: {} '.format(self._player_name))
        self._name_label.pack(side=tk.RIGHT)

    def set_game(self, game_mode):
        """Set game mode label"""
        self._game_label.config(text=game_mode+' Mode')

    def set_score(self, score):
        """Set current score label"""
        self._score_label.config(text='Score: '+str(score))


class LoloLogo(tk.Canvas):
    """Class for setting the game logo."""
    def __init__(self, logo_frame):
        """Constructor

        Parameters:
            logo_frame (tk.Tk|tk.Frame): The parent widget.
        """
        super().__init__()
        self._logo_frame = logo_frame
        self._canvas = tk.Canvas(self._logo_frame, width=332, height=130)
        self.draw()
        self._canvas.pack(side=tk.TOP)

    def draw(self):
        """Draw the logo"""
        self._canvas.create_line(30, 10, 30, 100, 80, 100, width=25, fill='#9966ff')
        self._canvas.create_oval(100, 45, 155, 100, width=25, outline='#9966ff')
        self._canvas.create_line(195, 10, 195, 100, 245, 100, width=25, fill='#9966ff')
        self._canvas.create_oval(265, 45, 320, 100, width=25, outline='#9966ff')


class ObjectiveGame(RegularGame):
    """Objective game of Lolo.

    Join groups of three or more until max tiles are formed. Join max tiles to
    destroy all surrounding tiles."""

    GAME_NAME = "Objective"

    def __init__(self, size=(8, 8), types=3, min_group=3,
                 max_tile_value=50, max_tile_type='max', normal_weight=20,
                 max_weight=2, animation=True, autofill=True):
        """Constructor

        Parameters:
            size (tuple<int, int>): The number of (rows, columns) in the game.
            types (int): The number of types of basic tiles.
            min_group (int): The minimum number of tiles required for a
                            connected group to be joinable.
            normal_weight (int): The relative weighted probability that a basic
                                tile will be generated.
            max_weight (int): The relative weighted probability that a maximum
                            tile will be generated.
            animation (bool): If True, animation will be enabled.
            autofill (bool): Automatically fills the grid iff True.
        """
        self._file = "objective.json"
        self._data = {}
        self.load()
        self._sizex = 6
        self._sizey = 6
        self._size = (self._sizex, self._sizey)
        self._types = types
        self._min_group = min_group
        self._starting_grid = []
        self._objectives = []
        self._limit = 90
        self.decode()

        super().__init__(self._size, self._types, self._min_group,
                 max_tile_value, max_tile_type, normal_weight,
                 max_weight, animation, autofill)

    def _load_json(self):
        """Loads the objective json file."""
        with open(self._file, 'r') as file:
            data = json.load(file)
        return data

    def load(self):
        """Loads the objective information from the objective file into the
        manager.
        """
        self._data = self._load_json()
        print(self._data)

    def decode(self):
        """Decode objective information"""
        self._types = self._data["types"]
        self._sizex = self._data["sizex"]
        self._sizey = self._data["sizey"]
        self._size = (self._sizex, self._sizey)
        self._min_group = self._data["min_group"]
        self._limit = self._data["limit"]


class ObjectiveGameMode(LoloApp):
    """Class for a objective game."""
    def __init__(self, master, game=ObjectiveGame(), grid_view=None, playername=None):
        """Constructor

        Parameters:
            master (tk.Tk|tk.Frame): The parent widget.
            game (model.AbstractGame): The game to play. Defaults to a
                                        ObjectiveGame.
            grid_view (view.GridView): The view to use for the game. Optional.
            playername (string): The current player's name. Default is None.
        """
        self._master = master
        self._game = game
        print(self._game)
        super().__init__(self._master, self._game, grid_view, playername)
        self._master.title('Lolo :: ' + self._game.get_name() + ' Game')


class MainWindow():
    """Loading Screen."""
    def __init__(self, master):
        """Constructor

        Parameters:
            master (tk.Tk|tk.Frame): The parent widget.
        """
        self._master = master
        self._game_mode = RegularGame()

        # Background music, only work on Windows
        winsound.PlaySound("./Nier.wav", winsound.SND_FILENAME|winsound.SND_ASYNC)

        # Logo frame
        logo_frame = tk.Frame(self._master)
        logo_frame.pack(side=tk.TOP)
        logo = LoloLogo(logo_frame)

        # Input frame
        input_frame = tk.Frame(self._master)
        input_frame.pack(side=tk.TOP, pady=10)
        name_label = tk.Label(input_frame, text="Your Name: ")
        name_label.pack(side=tk.LEFT)
        self._name_text = tk.Entry(input_frame)
        self._name_text.pack(side=tk.LEFT)

        # Button Frame
        button_frame = tk.Frame(self._master)
        button_frame.pack(side=tk.LEFT, expand=True, padx=100)

        bt_playgame = tk.Button(button_frame, text="New Game", command=self.startgame)
        bt_playgame.pack(side=tk.TOP, ipadx=100, pady=30)
        bt_selectmode = tk.Button(button_frame, text="Game Mode", command=self.gamemodewindow)
        bt_selectmode.pack(side=tk.TOP, ipadx=100, pady=30)
        bt_selectmode = tk.Button(button_frame, text="Objective Mode", command=self.startobjectivegame)
        bt_selectmode.pack(side=tk.TOP, ipadx=100, pady=30)
        bt_highscore = tk.Button(button_frame, text="High Score", command=self.highscorewindow)
        bt_highscore.pack(side=tk.TOP, ipadx=100, pady=30)
        bt_exitgame = tk.Button(button_frame, text="Exit Game", command=quit)
        bt_exitgame.pack(side=tk.TOP, ipadx=100, pady=30)

        # Auto play frame
        self._autogame_frame = tk.Frame(self._master)
        self._autogame_frame.pack(side=tk.RIGHT, expand=True, padx=20, pady=10)
        self._auto_game2 = AutoPlayingGame(self._autogame_frame, RegularGame())

    def startgame(self):
        """Start selected Lolo game."""
        if str(self._name_text.get()) != "":
            self._auto_game2._grid_view.off('resolve', self._auto_game2.resolve)
            root = tk.Toplevel()
            app = LoloApp(root, self._game_mode, None, str(self._name_text.get()))
        else:
            messagebox.showinfo(title="No Name", message="Please input a name!")

    def startobjectivegame(self):
        """Start Objective Lolo game."""
        if str(self._name_text.get()) != "":
            self._auto_game2._grid_view.off('resolve', self._auto_game2.resolve)
            root = tk.Toplevel()
            app = LoloApp(root, ObjectiveGame(), None, str(self._name_text.get()))
        else:
            messagebox.showinfo(title="No Name", message="Please input a name!")

    def gamemodewindow(self):
        """Show game mode select window."""
        gm = GameModeWindow(self)

    def highscorewindow(self):
        """Show high score window."""
        hs = HighScoreWindow()


class AutoPlayingGame(BaseLoloApp):
    """Class for auto play Lolo game."""
    def __init__(self, master, game=None, grid_view=None):
        """Constructor

        Parameters:
            master (tk.Tk|tk.Frame): The parent widget.
            game (model.AbstractGame): The game to play. Defaults to a
                                        game_regular.RegularGame.
            grid_view (view.GridView): The view to use for the game. Optional.
        """
        super().__init__(master, game, grid_view)
        self._move_delay = 1000
        self.resolve()

    def bind_events(self):
        """Binds relevant events."""
        self._game.on('resolve', self.resolve)
        self._game.off('score', self.score)
        self._grid_view.off('select', self.activate)
        self._game.on('game_over', self.game_over)

    def resolve(self, delay=None):
        """Makes a move after a given movement delay."""
        if delay is None:
            delay = self._move_delay
        self._master.after(delay, self.move)

    def move(self):
        """Finds a connected tile randomly and activates it."""
        connections = list(self._game.find_groups())
        if connections:
            # pick random valid move
            cells = list()
            for connection in connections:
                for cell in connection:
                    cells.append(cell)
            self.activate(random.choice(cells))
        else:
            self.game_over()

    def score(self, score):
        """Handles the score."""
        pass

    def reset(self):
        """Handles the reset."""
        pass

    def game_over(self):
        """Handles the game ending."""
        self._game.reset()
        self._grid_view.draw(self._game.grid, self._game.find_connections())
        self.resolve(self._move_delay)


class HighScoreWindow(MainWindow):
    """High Score Screen."""
    def __init__(self):
        """Constructor."""
        score = highscores.HighScoreManager()
        highestdata = score.get_sorted_data()[0]
        highestgrid = highestdata['grid']
        highestname = highestdata['name']
        highestscore = highestdata['score']
        game = RegularGame.deserialize(highestgrid)

        data = score.get_sorted_data()
        name_list = []
        score_list = []

        for i in range(len(data)):
            name_list.append(data[i]['name'])
            score_list.append(str(data[i]['score']))

        print(name_list)

        score_window = tk.Toplevel()
        score_window.title("High Scores :: Lolo")

        bestplayer = tk.Label(score_window, text="Best Player: {} with {} points!".format(highestname, highestscore))
        bestplayer.pack(side=tk.TOP)

        sw = BaseLoloApp(score_window, game)
        sw._grid_view.off('select', sw.activate)

        leaderboard = tk.Label(score_window, text="Leaderboard")
        leaderboard.pack(side=tk.TOP)

        name_frame = tk.Frame(score_window)
        name_frame.pack(side=tk.LEFT)
        score_frame = tk.Frame(score_window)
        score_frame.pack(side=tk.RIGHT)

        # Create leaderboard
        for text in name_list:
            tk.Label(name_frame, text=text).pack(side=tk.TOP, anchor=tk.W)
        for score in score_list:
            tk.Label(score_frame, text=score).pack(side=tk.TOP, anchor=tk.E)


class GameModeWindow(MainWindow):
    """Game mode selection window."""
    def __init__(self, mw):
        """Constructor

        Parameters:
            mw (MainWindow): Mainwindow element.
        """
        self._mw = mw
        self._gamemode_root = tk.Toplevel()

        self._gamemode_root.title("Game Modes :: Lolo")

        text = [("Regular", 1),
                ("Make 13", 2),
                ("Lucky 7", 3),
                ("Unlimited", 4)]

        gamemode_frame = tk.Frame(self._gamemode_root)
        gamemode_frame.pack(side=tk.LEFT)

        self._gamemode_dict = {1: RegularGame(), 2: Make13Game(), 3: Lucky7Game(), 4: UnlimitedGame()}
        # Find the default value
        self._gamemode_dict_reverse = {type(RegularGame()): 1, type(Make13Game()): 2, type(Lucky7Game()): 3, type(UnlimitedGame()): 4}

        self._save = self._gamemode_dict_reverse[type(self._mw._game_mode)]

        self._game_select = tk.IntVar()
        self._game_select.set(self._save)

        for t, v in text:
            tk.Radiobutton(gamemode_frame,
                           text=t,
                           variable=self._game_select,
                           value=v,
                           command=lambda: self.showauto(self._gamemode_dict[self._game_select.get()])
                           ).pack(side=tk.TOP, padx=200, pady=30)

        tk.Button(gamemode_frame, text="Save", command=self.setgame).pack(side=tk.TOP, padx=200, pady=30)

        self._game_frame = tk.Frame(self._gamemode_root)
        self._game_frame.pack(side=tk.RIGHT, expand=True, padx=20, pady=10)
        self._auto_game = AutoPlayingGame(self._game_frame, self._gamemode_dict[self._game_select.get()])

    def setgame(self):
        """Set game mode."""
        self._mw._game_mode = self._gamemode_dict[self._game_select.get()]
        print(self._mw._game_mode)

        self._auto_game._game.off('resolve', self._auto_game.resolve)

    def showauto(self, gamemode):
        """Show auto playing game with selected mode."""
        print(gamemode)
        self._auto_game._game.off('resolve', self._auto_game.resolve)
        self._game_frame.destroy()
        self._game_frame = tk.Frame(self._gamemode_root)
        self._game_frame.pack(side=tk.RIGHT, expand=True, padx=20, pady=10)
        self.startplay(gamemode)

    def startplay(self, gamemode):
        """Change auto playing game with selected mode."""
        self._auto_game = AutoPlayingGame(self._game_frame, gamemode)


def main():
    # Your GUI instantiation code here
    root = tk.Tk()
    root.title("LoLo")

    main_window = MainWindow(root)

    root.mainloop()


if __name__ == "__main__":
    main()
