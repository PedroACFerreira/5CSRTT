
import threading
from os import getcwd, path, rename, listdir, walk, kill
from sys import path as syspath
from pathlib import Path
from tkinter.scrolledtext import ScrolledText
from natsort import natsorted

dir_path = getcwd()
for dir_name in [x[0] for x in walk(dir_path)]:
    if path.isdir(dir_name):
        syspath.insert(0, dir_name)

from PIL import ImageTk
from Packages.Tooltips import *
from Packages.tkintertablez import *
from configparser import ConfigParser
from Packages.FCSRTT_FT235H import FCSRTT
from multiprocessing import Process, Queue, Event

from signal import SIGTERM # Sys commands

class Inator():

    def __init__(self, root):

        self.root = root
        root.title("5-CSRTT - PDBEB Course Demo")

        def center_root(width=300, height=200):
            # get screen width and height
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            self.root.minsize(width, height)
            # calculate position x and y coordinates
            x = (screen_width / 2) - (width / 2)
            y = (screen_height / 2) - (height / 2) - 100
            self.root.geometry('%dx%d+%d+%d' % (width, height, x, y))

        center_root(800, 650)
        root.iconbitmap(Path(dir_path + "/Inator_Ico.ico"))
        root.rowconfigure(0, weight=1)
        root.columnconfigure(2, weight=1)
        root.configure(background='#F8F8FF')
        root.rowconfigure(0, weight=1)
        self.Setup_cohort_data()
        self.Setup_Styles()

        self.mainFrameLabel = Label(text='Main', style="LabelStyleMain.TLabel", background=self.FrameColorMain,
                                    padding=[0, 5, 0, 5])
        self.mainFrame = LabelFrame(root, labelwidget=self.mainFrameLabel, padding=[20, 0, 50, 0],
                                    style="self.mainFrameStyle.TFrame")
        self.mainFrame.grid(row=0, column=2, sticky="nsew")

        self.sideFrame = Frame(root, width=100, padding=[0, 10, 0, 10], style="self.sideFrameStyle.TFrame")
        self.sideFrame.grid(row=0, rowspan=2, column=0, pady=(8, 0), sticky="nsw")
        self.sideFrame.columnconfigure(0, weight=1)

        self.scrollFrame = Frame(root, height=50, style='self.sideFrameStyle.TFrame')
        self.scrollFrame.grid(row=1, column=1, columnspan=2, sticky='swe')
        self.scrollFrame.columnconfigure(0, weight=1)

        self.Sep = Separator(root, orient="vertical").grid(column=1, row=0, rowspan=2, sticky="nws")

        self.Side_bar()
        self.Menu_bar()
        self.Scroll_text()
        self.read_config()

    def read_config(self):

        self.GPIO = self.config_file["GPIO"]
        self.Trial = self.config_file["Trial Configuration"]

        m = self.GPIO['step_motor'].split(',')
        self.in1, self.in2, self.in3, self.in4 = m[0], m[1], m[2], m[3]
        sr = self.GPIO["serial_reg"].split(',')
        self.ser, self.rclk, self.srclk = sr[0], sr[1], sr[2]
        self.IREm = self.GPIO['ir_emmiter']
        ir = self.GPIO["ir_receiver"].split(',')
        self.IR1, self.IR2, self.IR3, self.IR4, self.IR5 = ir[0], ir[1], ir[2], ir[3], ir[4]
        self.LK = self.GPIO['lickometer']
        self.LGTNo = self.GPIO['nr_lights']
        self.NSR = self.GPIO['nr_of_reg']
        HL = self.GPIO["ser_reg_holepins"].split(',')
        self.HL1, self.HL2, self.HL3, self.HL4, self.HL5 = HL[0], HL[1], HL[2], HL[3], HL[4]
        Amb = self.GPIO["ser_reg_ambientpins"].split(',')
        self.AmbL1, self.AmbL2, self.AmbL3, self.AmbL4 = Amb[0], Amb[1], Amb[2], Amb[3]
        self.RWLi = self.GPIO['ser_reg_reward']
        self.ttyp = self.Trial['trial type']
        self.tdur = self.Trial['trial duration']
        self.crit = self.Trial['criterion']
        self.ITI = self.Trial['iti']
        self.TO = self.Trial['to']
        self.LH = self.Trial['lh']
        self.SD = self.Trial['sd']

    def Setup_cohort_data(self):

        ## Config file read/setup ##

        # Get the configparser object
        self.config_file = ConfigParser()

        if not path.exists('config.ini'):
            # Pin order starting at index 0 <C0,C1,C2,C3,C4,C5,C6,C7,D4,D5,D6,D7>
            # Serial Register pins go from 1 to 15, excluding 8
            self.config_file["GPIO"] = {
                "step_motor": "8,9,10,11",
                "serial_reg": "2,1,0",
                "nr_of_reg": "2",
                "ir_emmiter": "11",
                "ir_receiver": "7,6,5,4,3",
                "lickometer": "11",
                "nr_lights": "10",
                "ser_reg_holepins": "5,6,7,8,9",
                "ser_reg_ambientpins": "1,2,3,4",
                "ser_reg_reward": "10"
            }
            self.config_file["Trial Configuration"] = {
                "trial type": "habituation",
                "trial duration": '30',
                "criterion": '50',
                "iti": '2',
                "lh": '30',
                "sd": '30',
                'to': '2'
            }
            self.config_file["Cohort Data"] = {
                "last cohort": "eg_cohort",

            }

            with open('config.ini', 'w') as conf:
                self.config_file.write(conf)

        self.config_file.read("config.ini")
        # read_config()

        ## Cohort Data ##
        self.Cohort_dict_template = {'ID': '', 'Gender': '', 'Cond': '', 'Habituation': '', 'Train 1': '',
                                     'Train 2': '',
                                     'Test': '', 'Identifier': '0001'}
        self.Animal_dict_template = {'Day': '1', 'Trial Type': 'Habituation', 'Total Trials': '', 'Time': '',
                                     'Correct': '', 'Fail': '', 'Precision': '', 'Omissions': '',
                                     'Rep Errors': '', 'Premature Errors': '', 'TO Errors': '',
                                     'ITI': '', 'TO': '', 'SD': '', 'LH': ''}
        self.Day_dict_template = {'Trial': '1', 'Hole': '', 'Hole pressed': '',
                                  'Time to press': '', 'Outcome': '', 'Time to reward': '',
                                  'Error': '', 'Error Type': '', 'Error Presses': ''}

        ext = '.pickle'
        self.curr_cohort = self.config_file['Cohort Data']['last cohort']
        self.cohort_var = StringVar(value=self.curr_cohort)
        self.animal_var = StringVar()
        self.tabletype = 'Cohort'
        self.cohort_list = [f.replace(ext, "") for f in listdir(dir_path + '\\Cohort_data') if
                            (path.isfile(path.join(dir_path + '\\Cohort_data', f)) and f.endswith(ext))]

        if not os.listdir(dir_path + '\\Cohort_data'):
            eg_cohort = {
                'cohort': {
                    1: {'ID': 'FE', 'Gender': 'Male', 'Cond': 'Ctrl', 'Habituation': '', 'Train 1': '', 'Train 2': '',
                        'Test': '', 'Identifier': '0001'},
                    2: {'ID': 'TD', 'Gender': 'Female', 'Cond': 'IL-4', 'Habituation': '', 'Train 1': '', 'Train 2': '',
                        'Test': '', 'Identifier': '0002'}},
                '0001': {'FE': {
                                1: {'Day': '1', 'Trial Type': 'Habituation', 'Total Trials': '50', 'Time': '28:55',
                                     'Correct': '22', 'Fail': '18', 'Accuracy': '55%', 'Omissions': '10',
                                     'Rep Errors': '0', 'Premature Errors': '0', 'TO Errors': '0',
                                     'ITI': '5', 'TO': '0', 'SD': '30', 'LH': '30'},
                                2: {'Day': '2', 'Trial Type': 'Train1', 'Total Trials': '', 'Time': '',
                                     'Correct': '', 'Fail': '', 'Accuracy': '', 'Omissions': '',
                                     'Rep Errors': '', 'Premature Errors': '', 'TO Errors': '',
                                     'ITI': '', 'TO': '', 'SD': '', 'LH': ''}},
                          '1': {
                                1: {'Trial': '1', 'Hole': '', 'Hole pressed': '',
                                    'Time to press': '', 'Outcome': '', 'Time to reward': '',
                                    'Error': '', 'Error Type': '', 'Error Presses': ''}}},
                '0002': {'TD': {
                                1: {'Day': '1', 'Trial Type': 'Habituation', 'Total Trials': '50', 'Time': '27:22',
                                     'Correct': '27', 'Fail': '15', 'Accuracy': '64.28%', 'Omissions': '8',
                                     'Rep Errors': '0', 'Premature Errors': '0', 'TO Errors': '0',
                                     'ITI': '5', 'TO': '0', 'SD': '30', 'LH': '30'}},
                         '1': {
                                1: {'Trial': '1', 'Hole': '', 'Hole pressed': '',
                                    'Time to press': '', 'Outcome': '', 'Time to reward': '',
                                    'Error': '', 'Error Type': '', 'Error Presses': ''}
                }}
            }

            with open(dir_path + '\\Cohort_data\\eg_cohort.pickle', 'wb') as handle:
                pickle.dump(eg_cohort, handle, protocol=pickle.HIGHEST_PROTOCOL)

            with open(dir_path + '\\Cohort_data\\eg_cohort.pickle', 'rb') as handle:
                self.full_data = pickle.load(handle)
            self.cohort_data = self.full_data['cohort']
            self.curr_cohort = 'eg_cohort'
            self.config_file["Cohort Data"]['last cohort'] = self.curr_cohort
            with open('config.ini', 'w') as conf:
                self.config_file.write(conf)
            IDList = [self.full_data['cohort'][i]['Identifier'] for i in self.full_data['cohort']]
            print('Eg_cohort data created')

        else:

            try:
                with open(dir_path + '\\Cohort_data\\' + self.curr_cohort + '.pickle', 'rb') as handle:
                    self.full_data = pickle.load(handle)
                self.cohort_data = self.full_data['cohort']

            except:
                with open(dir_path + '\\Cohort_data\\' + self.cohort_list[0] + '.pickle', 'rb') as handle:
                    full_data = pickle.load(handle)
                    cohort_data = full_data['cohort']
                    cohort_var = StringVar(value=self.cohort_list[0])
                self.config_file["Cohort Data"]['last cohort'] = self.cohort_list[0]

            self.IDList = [self.full_data['cohort'][i]['Identifier'] for i in self.full_data['cohort']]

    def Setup_Styles(self):
        ## Styles ##

        # Assets

        # Colors

        self.sideFrameButton_Color = '#8AB1DB'
        self.sideFrameButton_Color2 = '#6d98c7'
        self.FrameColorMain = '#F8F8FF'
        self.FrameColorSide = '#F8F8FF'
        self.FrameColorEntry = '#dfe4eb'
        self.FrameColorEntry2 = '#a3aab5'
        self.SideSeparator = '#688aab'

        # Theme Level Style

        self.s = Style()

        self.s.theme_use('default')

        self.s.map("TEntry", fieldbackground=[("active", "white"), ("disabled", "white")])
        self.s.theme_settings("default",
                              {'Btt.TButton': {'configure': {},
                                               "map":
                                                   {"background": [("active", self.sideFrameButton_Color2),
                                                                   ("!disabled", self.sideFrameButton_Color)]}}})
        self.s.theme_settings("default",
                              {'Side.TSeparator': {
                                  'configure': {'background': self.SideSeparator, 'orient': 'horizontal'},
                                  }})
        self.s.theme_settings("default",
                              {'RBtt.TRadiobutton': {'configure': {},
                                                     "map":
                                                         {"background": [("active", self.FrameColorEntry2),
                                                                         ("!disabled", self.FrameColorEntry)]}}})
        self.s.theme_settings("default",
                              {'Btt.TCombobox': {"configure": {"padding": 2, 'insertwidth':0},
                                                   "map": {'selectbackground':'white',
                                                       "background": [("active", self.sideFrameButton_Color2),
                                                                      ("!disabled", self.sideFrameButton_Color)],
                                                       "fieldbackground": [("active", self.sideFrameButton_Color2),
                                                                           ("!disabled", self.sideFrameButton_Color)],
                                                       "foreground": [("focus", 'white'),
                                                                      ("!disabled", 'white')]
                                                               }
                                                           }
                                                        })

        # This removes the black inside border showing up after click

        Buttonlayout = [('Button.button', {'sticky': 'nswe', 'children': [
            ('Button.padding', {'sticky': 'nswe', 'children': [('Button.label', {'sticky': 'nswe', })]})]})]

        Radiobuttonlayout = [('Radiobutton.padding', {'sticky': 'nswe', 'children':
            [('Radiobutton.indicator', {'side': 'left'}),
             ('Radiobutton.label', {'sticky': 'nswe'}
              )]}
                              )]

        ComboboxLayout = [('Combobox.border', {'sticky' : 'nswe',
                                              'children' : [(

                                                  'Combobox.padding', {

                                                    'sticky' : 'nswe',
                                                    'children' : [(
                                                        'Combobox.background', {
                                                          'sticky' : 'nswe',
                                                          'children' : [(

                                                                    'Combobox.textarea', {
                                                                      'sticky' : 'nswe',
                                                                    }
                                                                )]
                                                              }
                                                          )]
                                                        }
                                                    )]
                                                  }
                                              )]


        self.s.layout('Btt.TButton', Buttonlayout)
        self.s.layout('RBtt.TRadiobutton', Radiobuttonlayout)
        self.s.layout('Btt.TCombobox', ComboboxLayout)

        # Frame

        self.s.configure('mainFrameStyle.TFrame', background=self.FrameColorMain)
        self.s.configure('sideFrameStyle.TFrame', background=self.FrameColorSide)
        self.s.configure('EntryFrameStyle.TFrame', background=self.FrameColorEntry)

        # Labels
        self.s.configure('LabelStyleMain.TLabel', background=self.FrameColorMain, font=('Myriad', 12))
        self.s.configure('LabelStyleSide.TLabel', background=self.FrameColorSide, font=('Myriad', 12))
        self.s.configure('EntryStyle.TLabel', background=self.FrameColorEntry, font=('Myriad', 12))
        self.s.configure('EntryFrameStyle.TLabel', background=self.sideFrameButton_Color, font=('Myriad', 12, 'bold'))

        # Buttons

        self.s.configure('SideFrameButton.Btt.TButton', foreground='white', font=('Myriad', 12, 'bold'))
        self.s.configure('Combo.Btt.TButton', foreground='white', font=('Myriad', 14, 'bold'),
                         selectbackground=self.sideFrameButton_Color2, )
        self.s.configure('Combo.Cmb.TCombobox', font=('Myriad', 12, 'bold'))
        self.s.configure('mainFrameButton.TLabel', font=('Myriad', 12, 'bold'), borderwidth='0',
                         background=self.FrameColorMain)
        self.s.configure('RBtt.TRadiobutton', font=('Myriad', 11))

    def ctrlc(self, event=None):
        if self.mainFrameLabel.cget('text') == 'Cohort Data':
            self.table.ctrlCopy(event)
    def ctrlv(self, event=None):
        if self.mainFrameLabel.cget('text') == 'Cohort Data':
            self.table.ctrlPaste(event)
    def ctrlx(self, event=None):
        if self.mainFrameLabel.cget('text') == 'Cohort Data':
            self.table.ctrlx(event)
    def ctrlz(self, event=None):
        if self.mainFrameLabel.cget('text') == 'Cohort Data':
            self.table.doundo(event)
    def ctrlshiftz(self, event=None):
        if self.mainFrameLabel.cget('text') == 'Cohort Data':
            self.table.ctrlshiftz(event)

    def Menu_bar(self):
        # ## Menu bar ##

        # File Menu
        self.menubar = Menu(self.root)
        self.fileMenu = Menu(self.menubar, tearoff=0)
        self.fileMenu.add_command(label="New Project", command=lambda: print('in progress'))
        self.fileMenu.add_command(label="Open Project", command=lambda: print('in progress'))
        self.fileMenu.add_command(label="Save", command=lambda: print('in progress'))
        self.fileMenu.add_command(label="Save as...", command=lambda: print('in progress'))
        self.fileMenu.add_command(label="Close Project", command=lambda: print('in progress'))
        self.fileMenu.add_separator()  ##-----------##
        self.fileMenu.add_command(label="Destroy Inator", command=self.root.quit)
        self.menubar.add_cascade(label="File", menu=self.fileMenu)

        # Edit Menu
        self.editMenu = Menu(self.menubar, tearoff=0)
        self.editMenu.add_command(label="Undo", command = self.ctrlz)
        self.editMenu.add_command(label="Redo(Ctrl+shfit+z)", command = self.ctrlshiftz)
        self.editMenu.add_separator()  ##-----------##
        self.editMenu.add_command(label="Cut (Ctrl+x)", command=self.ctrlx)
        self.editMenu.add_command(label="Copy (Ctrl+c)", command=self.ctrlc)
        self.editMenu.add_command(label="Paste (Ctrl+v)", command=self.ctrlv)
        self.editMenu.add_separator()  ##-----------##
        self.editMenu.add_command(label="Settings", command=lambda: print('in progress'))

        ##Setup Menu

        self.menubar.add_cascade(label="Edit", menu=self.editMenu)
        self.helpmenu = Menu(self.menubar, tearoff=0)
        self.helpmenu.add_command(label="Help", command=lambda: print('in progress'))

        def create_about():
            about = Toplevel(bg='white', highlightbackground="#457A83", highlightcolor="#457A83", highlightthickness=4)
            center_toplevel(about)
            aboutimg = ImageTk.PhotoImage(file=Path(dir_path + "/Assets/About.jpg"))
            # Remove border/buttons from about window
            about.overrideredirect(1)

            # Set focus on the about windows so we can <Leave> in .bind
            about.focus_set()

            aboutlabel = Label(about, image=aboutimg, borderwidth=0, background='white', anchor='center')
            aboutlabel.photo = aboutimg
            aboutlabel.grid(row=0, column=0, padx=(5, 0), sticky='wns')
            aboutlabeltext = Label(about, anchor='center',
                                   text='5-CSRTT-Inator\nVersion 0.1\n\nIn Development\n\n\nBy Pedro Ferreira\n@CNC-NCBL',
                                   justify='center', padding=[5, 0, 0, 0], background='#C1D4DB',
                                   font=('Myriad', 12, 'bold'))
            aboutlabeltext.grid(row=0, column=1, padx=(10, 0), sticky='nsew')
            about.rowconfigure(0, weight=1)
            about.columnconfigure(1, weight=1)

            # Make a button press outside the window destroy it
            about.bind("<Leave> <Button>", about.destroy)

        def center_toplevel(win, width=400, height=300, xp=0.5, yp=0.6):
            x = self.root.winfo_x()
            y = self.root.winfo_y()
            xwidth = self.root.winfo_width()
            yheight = self.root.winfo_height()
            nx = x + xp * xwidth - width / 2
            ny = y + yp * yheight - height / 2
            win.geometry('%dx%d+%d+%d' % (width, height, nx, ny))

        self.helpmenu.add_command(label="About...", command=create_about)
        self.menubar.add_cascade(label="Help", menu=self.helpmenu)

        self.root.config(menu=self.menubar)

    def Side_bar(self):
        ## Side Build##

        sideFrameLabel = Label(self.sideFrame, text='5CSRTT', style='LabelStyleSide.TLabel')
        sideFrameLabel.grid(row=0, column=0, padx=10, pady=(0, 10))

        Separator(self.sideFrame, style='Side.TSeparator').grid(column=0, row=1, padx=1, sticky="we")
        self.Home_button = Button(self.sideFrame, text="Home", style="SideFrameButton.Btt.TButton", command=self.Home)
        self.Home_button.grid(row=2, column=0, padx=2, pady=1, sticky="ew")
        Separator(self.sideFrame, style='Side.TSeparator').grid(column=0, row=3, padx=1, pady=1, sticky="we")
        self.IOSetup_button = Button(self.sideFrame, text="IO Setup", style="SideFrameButton.Btt.TButton",
                                     command=self.IO_Setup)
        self.IOSetup_button.grid(row=4, column=0, padx=2, pady=(0, 1), sticky="ew")
        Separator(self.sideFrame, style='Side.TSeparator').grid(column=0, row=5, padx=1, pady=1, sticky="we")
        self.CohortConf_button = Button(self.sideFrame, text="Config Cohort", style="SideFrameButton.Btt.TButton",
                                        command=self.Config_Cohort)
        self.CohortConf_button.grid(row=6, column=0, padx=2, pady=(0, 1), sticky="ew")
        Separator(self.sideFrame, style='Side.TSeparator').grid(column=0, row=7, padx=1, pady=1, sticky="we")
        self.TrialConf_button = Button(self.sideFrame, text="Trial Config", style="SideFrameButton.Btt.TButton",
                                       command=self.Trial_Config)
        self.TrialConf_button.grid(row=8, column=0, padx=2, pady=(0, 1), sticky="ew")
        Separator(self.sideFrame, style='Side.TSeparator').grid(column=0, row=9, padx=1, pady=1, sticky="we")

    def Scroll_text(self):

        ## ScrollText Build##

        def copy_paste_cut_show(e):
            the_menu = Menu(self.root, tearoff=0)
            the_menu.add_command(label="Cut")
            the_menu.add_command(label="Copy")
            the_menu.add_command(label="Paste")
            w = e.widget
            the_menu.entryconfigure("Cut",
                                    command=lambda: w.event_generate("<<Cut>>"))
            the_menu.entryconfigure("Copy",
                                    command=lambda: w.event_generate("<<Copy>>"))
            the_menu.entryconfigure("Paste",
                                    command=lambda: w.event_generate("<<Paste>>"))
            the_menu.tk.call("tk_popup", the_menu, e.x_root, e.y_root)

        self.text_area = ScrolledText(self.scrollFrame, wrap=WORD, width=40, height=10, font=("Myriad", 10))
        self.text_area.grid(column=0, sticky='nswe')
        self.text_area.bind("<Button-3><ButtonRelease-3>", copy_paste_cut_show)
        Clear_button = Button(self.scrollFrame, text="Clear", style="SideFrameButton.Btt.TButton",
                              command=lambda: self.text_area.delete('1.0', END))
        Clear_button.grid(column=0, row=1, padx=2, pady=(0, 1), sticky="e")



    def Home(self):
        for widget in self.mainFrame.winfo_children():
            widget.destroy()
        self.mainFrameLabel.config(text='Main', padding=[0, 5, 0, 5])

    def IO_Setup(self):
        for widget in self.mainFrame.winfo_children():
            widget.destroy()

        self.mainFrameLabel.config(text='IO Configuration', padding=[0, 5, 0, 15])

        def test_Val_IO(inStr, acttyp):  # Function to validate Entry widget input as digits
            if acttyp == '1':
                if not inStr.isdigit():
                    return False
                elif int(inStr) > 40:
                    return False
            return True

        vcmdIO = self.mainFrame.register(test_Val_IO), '%P', '%d'  # Command to check if input is digits
        # Stepper motor pins
        motorFrameLabel = Label(text='Motor', style="EntryFrameStyle.TLabel", background=self.FrameColorEntry,
                                padding=[0, 5, 0, 0])
        motorFrame = LabelFrame(self.mainFrame, labelwidget=motorFrameLabel, labelanchor='n',
                                style="EntryFrameStyle.TFrame")
        motorFrame.grid(row=0, column=0, sticky="nw")

        Label(motorFrame, text='IN1:', style='EntryStyle.TLabel').grid(row=0, column=0, padx=(10, 2), pady=(5, 0))
        self.m1 = Entry(motorFrame)
        self.m1.insert(0, self.in1)
        self.m1.grid(row=0, column=1, padx=(0, 5), pady=(5, 0))
        Label(motorFrame, text='IN2:', style='EntryStyle.TLabel').grid(row=0, column=3, padx=(0, 2), pady=(5, 0))
        self.m2 = Entry(motorFrame)
        self.m2.grid(row=0, column=4, padx=(0, 10), pady=(5, 0))
        self.m2.insert(0, self.in2)
        Label(motorFrame, text='IN3:', style='EntryStyle.TLabel').grid(row=1, column=0, padx=(10, 2), pady=(5, 5))
        self.m3 = Entry(motorFrame)
        self.m3.grid(row=1, column=1, padx=(0, 5), pady=(5, 5))
        self.m3.insert(0, self.in3)
        Label(motorFrame, text='IN4:', style='EntryStyle.TLabel').grid(row=1, column=3, padx=(0, 2), pady=(5, 5))
        self.m4 = Entry(motorFrame)
        self.m4.grid(row=1, column=4, padx=(0, 10), pady=(5, 5))
        self.m4.insert(0, self.in4)
        # Serial register pins

        SerialFrameLabel = Label(text='Serial Register', style="EntryFrameStyle.TLabel",
                                 background=self.FrameColorEntry,
                                 padding=[0, 5, 0, 0])
        SerialFrame = LabelFrame(self.mainFrame, labelwidget=SerialFrameLabel, labelanchor='n',
                                 style="EntryFrameStyle.TFrame")
        SerialFrame.grid(row=0, column=1, padx=15, sticky="n")

        Label(SerialFrame, text='SER:', style='EntryStyle.TLabel').grid(row=0, column=0, padx=(0, 2), pady=(5, 0))
        self.ser1 = Entry(SerialFrame)
        self.ser1.grid(row=0, column=1, padx=(0, 5), pady=(5, 0))
        self.ser1.insert(0, self.ser)
        Label(SerialFrame, text='RCLK:', style='EntryStyle.TLabel').grid(row=0, column=2, padx=(0, 10), pady=(5, 0))
        self.ser2 = Entry(SerialFrame)
        self.ser2.grid(row=0, column=3, padx=(0, 10), pady=(5, 0))
        self.ser2.insert(0, self.rclk)
        Label(SerialFrame, text='SRCLK:', style='EntryStyle.TLabel', padding=[20, 0, 0, 0]) \
            .grid(row=1, column=0, columnspan=2, padx=(10, 2), pady=(5, 0), sticky='e')
        self.ser3 = Entry(SerialFrame)
        self.ser3.grid(row=1, column=2, columnspan=2, padx=(10, 2), pady=(5, 5), sticky='w')
        self.ser3.insert(0, self.srclk)

        # Infrared Emmitter + Receivers
        IRFrameLabel = Label(text='IR Emmiter/Receivers', style="EntryFrameStyle.TLabel",
                             background=self.FrameColorEntry,
                             padding=[10, 5, 10, 0])
        IRFrame = LabelFrame(self.mainFrame, labelwidget=IRFrameLabel, style="EntryFrameStyle.TFrame")
        IRFrame.grid(row=1, column=0, padx=0, pady=15, sticky="nw", rowspan=2)
        Label(IRFrame, text='IR Emitter:', style='EntryStyle.TLabel') \
            .grid(row=0, column=0, columnspan=2, padx=(30, 2), pady=(5, 0))
        self.ir_em = Entry(IRFrame)
        self.ir_em.grid(row=0, column=2, columnspan=2, padx=(0, 0), pady=(5, 0))
        self.ir_em.insert(0, self.IREm)
        Label(IRFrame, text='IR1:', style='EntryStyle.TLabel').grid(row=2, column=0, padx=(20, 2), pady=(5, 0))
        self.ir1 = Entry(IRFrame)
        self.ir1.grid(row=2, column=1, padx=(0, 5), pady=(5, 0))
        self.ir1.insert(0, self.IR1)
        Label(IRFrame, text='IR2:', style='EntryStyle.TLabel').grid(row=2, column=2, padx=(0, 10), pady=(5, 0))
        self.ir2 = Entry(IRFrame)
        self.ir2.grid(row=2, column=3, padx=(0, 5), pady=(5, 0))
        self.ir2.insert(0, self.IR2)
        Label(IRFrame, text='IR3:', style='EntryStyle.TLabel').grid(row=3, column=0, padx=(20, 2), pady=(5, 0))
        self.ir3 = Entry(IRFrame)
        self.ir3.grid(row=3, column=1, padx=(0, 5), pady=(5, 0))
        self.ir3.insert(0, self.IR3)
        Label(IRFrame, text='IR4:', style='EntryStyle.TLabel').grid(row=3, column=2, padx=(0, 10), pady=(5, 0))
        self.ir4 = Entry(IRFrame)
        self.ir4.grid(row=3, column=3, padx=(0, 5), pady=(5, 5))
        self.ir4.insert(0, self.IR4)
        Label(IRFrame, text='IR3:', style='EntryStyle.TLabel').grid(row=4, column=0, padx=(20, 2), pady=(5, 0))
        self.ir5 = Entry(IRFrame)
        self.ir5.grid(row=4, column=1, padx=(0, 5), pady=(5, 5))
        self.ir5.insert(0, self.IR5)

        # Lickometer
        LickFrameLabel = Label(text='Lickometer', style="EntryFrameStyle.TLabel", background=self.FrameColorEntry,
                               padding=[10, 0, 10, 0])
        LickFrame = LabelFrame(self.mainFrame, labelwidget=LickFrameLabel, style="EntryFrameStyle.TFrame",
                               labelanchor='w')
        LickFrame.grid(row=2, column=0, padx=10, pady=15, sticky='sw')
        self.Lick = Entry(LickFrame)
        self.Lick.grid(row=0, column=0, padx=(5, 5), pady=(8, 7))
        self.Lick.insert(0, self.LK)

        # Light Config
        LightFrameLabel = Label(text='Light Config', style="EntryFrameStyle.TLabel", background=self.FrameColorEntry,
                                padding=[10, 10, 10, 0])
        LightFrame = LabelFrame(self.mainFrame, labelwidget=LightFrameLabel, style="EntryFrameStyle.TFrame",
                                labelanchor='n')
        LightFrame.grid(row=2, column=1, padx=10, pady=15, sticky='n')

        Label(LightFrame, text='# Lights', style='EntryStyle.TLabel').grid(row=0, column=0, columnspan=5, padx=(5, 2),
                                                                           pady=(5, 0))

        self.Light = Entry(LightFrame)
        self.Light.grid(row=0, column=5, columnspan=5, padx=(5, 5), pady=(5, 5))
        self.Light.insert(0, self.LGTNo)

        Label(LightFrame, text='# Registers', style='EntryStyle.TLabel').grid(row=1, column=0, columnspan=5,
                                                                              padx=(5, 5),
                                                                              pady=(5, 0))
        self.Reg = Entry(LightFrame)
        self.Reg.grid(row=1, column=5, columnspan=5, padx=(5, 5), pady=(5, 5))
        self.Reg.insert(0, self.NSR)

        Label(LightFrame, text='Hole Lights', style='EntryStyle.TLabel').grid(row=2, column=0, columnspan=10,
                                                                              padx=(0, 0),
                                                                              pady=(5, 0))
        self.Hole1 = Entry(LightFrame)
        self.Hole1.grid(row=3, column=0, padx=(10, 0), pady=(5, 5))
        self.Hole1.insert(0, self.HL1)
        Separator(LightFrame, style='Side.TSeparator', orient='vertical').grid(column=1, row=3, padx=1, pady=5,
                                                                               sticky="nsw")
        self.Hole2 = Entry(LightFrame)
        self.Hole2.grid(row=3, column=2, padx=(0, 0), pady=(5, 5))
        self.Hole2.insert(0, self.HL2)
        Separator(LightFrame, style='Side.TSeparator', orient='vertical').grid(column=3, row=3, padx=1, pady=5,
                                                                               sticky="nsw")
        self.Hole3 = Entry(LightFrame)
        self.Hole3.grid(row=3, column=4, padx=(0, 0), pady=(5, 5))
        self.Hole3.insert(0, self.HL3)
        Separator(LightFrame, style='Side.TSeparator', orient='vertical').grid(column=5, row=3, padx=1, pady=5,
                                                                               sticky="nsw")
        self.Hole4 = Entry(LightFrame)
        self.Hole4.grid(row=3, column=6, padx=(0, 0), pady=(5, 5))
        self.Hole4.insert(0, self.HL4)
        Separator(LightFrame, style='Side.TSeparator', orient='vertical').grid(column=7, row=3, padx=1, pady=5,
                                                                               sticky="nsw")
        self.Hole5 = Entry(LightFrame)
        self.Hole5.grid(row=3, column=8, columnspan=2, padx=(0, 0), pady=(5, 5),sticky='nsw')
        self.Hole5.insert(0, self.HL5)


        Label(LightFrame, text='Ambient', style='EntryStyle.TLabel').grid(row=4, column=0, columnspan=10, padx=(0, 0),
                                                                          pady=(5, 0))
        LightFrame.grid_columnconfigure(10, minsize=5)

        self.Amb1 = Entry(LightFrame)
        self.Amb1.grid(row=5, column=0, padx=(0, 0), pady=(5, 5),sticky="nse")
        self.Amb1.insert(0, self.AmbL1)
        Separator(LightFrame, style='Side.TSeparator', orient='vertical').grid(column=1, row=5, padx=1, pady=5,
                                                                               sticky="ns")
        self.Amb2 = Entry(LightFrame)
        self.Amb2.grid(row=5, column=2, padx=(0, 0), pady=(5, 5),sticky="ns")
        self.Amb2.insert(0, self.AmbL2)
        Separator(LightFrame, style='Side.TSeparator', orient='vertical').grid(column=3, row=5, padx=1, pady=5,
                                                                               sticky="ns")
        self.Amb3 = Entry(LightFrame)
        self.Amb3.grid(row=5, column=4, padx=(0, 0), pady=(5, 5),sticky="ns")
        self.Amb3.insert(0, self.AmbL3)
        Separator(LightFrame, style='Side.TSeparator', orient='vertical').grid(column=5, row=5, padx=1, pady=5,
                                                                               sticky="ns")
        self.Amb4 = Entry(LightFrame)
        self.Amb4.grid(row=5, column=6, columnspan=4, padx=(0, 0), pady=(5, 5),sticky="nsw")
        self.Amb4.insert(0, self.AmbL4)

        Label(LightFrame, text='Reward', style='EntryStyle.TLabel').grid(row=6, column=0, columnspan=10, padx=(0, 0),
                                                                         pady=(2, 0))

        self.RWL = Entry(LightFrame)
        self.RWL.grid(row=7, column=0, columnspan=10, padx=(0, 0), pady=(2, 5))
        self.RWL.insert(0, self.RWLi)

        # List of Entries

        self.SetupValues = [
            [self.m1, self.m2, self.m3, self.m4],
            [self.ser1, self.ser2, self.ser3],
            self.ir_em,
            [self.ir1, self.ir2, self.ir3, self.ir4, self.ir5],
            self.Lick,
            self.Light,
            self.Reg,
            [self.Hole1, self.Hole2, self.Hole3, self.Hole4, self.Hole5],
            [self.Amb1, self.Amb2, self.Amb3, self.Amb4],
            self.RWL
        ]

        for i in self.SetupValues:
            if type(i) is list:
                for f in i:
                    f.config(exportselection=0, font=('Myriad', 12), cursor='xterm', width=3, justify='center',
                             validate='key', validatecommand=vcmdIO)
            else:
                i.config(exportselection=0, font=('Myriad', 12), cursor='xterm', width=3, justify='center',
                         validate='key', validatecommand=vcmdIO)

        # Save Button

        def Save_IO():
            self.GPIO["step_motor"] = ",".join(i.get() for i in self.SetupValues[0])
            self.GPIO["serial_reg"] = ",".join(i.get() for i in self.SetupValues[1])
            self.GPIO["ir_emmiter"] = self.SetupValues[2].get()
            self.GPIO["ir_receiver"] = ",".join(i.get() for i in self.SetupValues[3])
            self.GPIO["lickometer"] = self.SetupValues[4].get()
            self.GPIO["nr_lights"] = self.SetupValues[5].get()
            self.GPIO["nr_of_reg"] = self.SetupValues[6].get()
            self.GPIO["ser_reg_holepins"] = ",".join(i.get() for i in self.SetupValues[7])
            self.GPIO["ser_reg_ambientpins"] = ",".join(i.get() for i in self.SetupValues[8])
            self.GPIO["ser_reg_reward"] = self.SetupValues[9].get()

            with open('config.ini', 'w') as conf:
                self.config_file.write(conf)

            self.config_file.read("config.ini")
            self.read_config()
            self.text_area.insert('end', "IO Settings Saved!\n")

        SaveButton = Button(self.mainFrame, text="Save", style="SideFrameButton.Btt.TButton",
                            command=Save_IO)
        SaveButton.grid(row=5, column=0, sticky='ws')

    def Config_Cohort(self, cohort=''):

        for widget in self.mainFrame.winfo_children():
            widget.destroy()

        self.cohort_list = [f.replace('.pickle', "") for f in listdir(dir_path + '\\Cohort_data') if
                            (path.isfile(path.join(dir_path + '\\Cohort_data', f)) and f.endswith('.pickle'))]

        self.mainFrameLabel.config(text='Cohort Data', padding=[0, 5, 0, 10])

        CohortFrame = Frame(self.mainFrame, style="EntryFrameStyle.TFrame")
        CohortFrame.pack(fill=BOTH, expand=True, pady=(0, 5))

        self.TableFrame = Frame(CohortFrame, style="EntryFrameStyle.TFrame")
        self.TableFrame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        TableButtonFrame = Frame(CohortFrame, style="EntryFrameStyle.TFrame")
        TableButtonFrame.grid(row=1, column=1, padx=5, pady=(0, 5))

        self.CohortButtonFrame = Frame(CohortFrame, style="EntryFrameStyle.TFrame")
        self.CohortButtonFrame.grid(row=0, column=0, rowspan=2, padx=(10, 0), pady=(0, 5), sticky='nswe')

        CohortFrame.rowconfigure(0, weight=1)
        CohortFrame.columnconfigure(1, weight=1)
        self.CohortButtonFrame.columnconfigure(0, weight=1)
        self.CohortButtonFrame.rowconfigure(7, weight=1)
        TableButtonFrame.columnconfigure(3, weight=1)
        TableButtonFrame.rowconfigure(0, weight=1)

        if cohort == '':
            self.Load_cohort(self.curr_cohort)
        else:
            self.Load_cohort(cohort)

        self.table = TableCanvas(self.TableFrame,
                                 cellwidth=100, cellbackgr='#FFFFFF',
                                 thefont=('Arial', 12), rowheight=25, rowheaderwidth=20,
                                 selectedcolor="#C8C8C8", multipleselectioncolor="#C8C8C8",
                                 rowselectedcolor='#C8C8C8', editable=True, data=self.cohort_data)

        self.table.show()
        self.table.bind('<Control-n>', self.table_addRows)
        self.tabletype = 'Cohort'


        # New Cohort

        self.NewCohortButton = Button(self.CohortButtonFrame, text="New Cohort", style="SideFrameButton.Btt.TButton",
                                      command=lambda: self.New_cohort())

        self.NewCohortButton.grid(row=1, column=0, padx=(2, 5), pady=(2, 0), sticky='nwes')

        # Rename Cohort

        self.RenameButton = Button(self.CohortButtonFrame, text="Rename Cohort", style="SideFrameButton.Btt.TButton",
                                   command=lambda: self.Rename_cohort())

        self.RenameButton.grid(row=7, column=0, padx=(2, 5), pady=(0, 10), sticky='ews')

        # Delete Cohort

        self.DeleteButton = Button(self.CohortButtonFrame, text="Delete Cohort", style="SideFrameButton.Btt.TButton",
                                   command=lambda: self.Delete_cohort())

        self.DeleteButton.grid(row=8, column=0, padx=(2, 5), pady=(0, 10), sticky='ews')

        # Select Cohort

        Label(self.CohortButtonFrame, text='Select Cohort', style='EntryStyle.TLabel').grid(row=2, column=0,
                                                                                       padx=(5, 2),
                                                                                       pady=(5, 0))
        self.SelectButton = Combobox(self.CohortButtonFrame, width=15, textvariable=self.cohort_var,
                                     values=natsorted(self.cohort_list),
                                     exportselection=0,
                                     state='readonly', style="Btt.TCombobox", justify=CENTER,
                                     font=('Myriad', 12, 'bold'))
        self.SelectButton.grid(row=3, column=0, padx=(2, 5), pady=(2, 0), sticky='nw')

        self.SelectButton.bind("<<ComboboxSelected>>", self.Select_cohort)

        # Select Animal
        Label(self.CohortButtonFrame, text='Select Animal', style='EntryStyle.TLabel').grid(row=4, column=0,
                                                                                       padx=(5, 2),
                                                                                       pady=(5, 0))

        self.AnimalButton = Combobox(self.CohortButtonFrame, width=15, textvariable=self.animal_var, values=[],
                                     postcommand=lambda: self.AnimalButton.config(values=self.drop_animal()),
                                     exportselection=0,
                                     state='readonly', style="Btt.TCombobox", justify=CENTER,
                                     font=('Myriad', 12, 'bold'), takefocus=False)
        self.AnimalButton.grid(row=5, column=0, padx=(2, 5), pady=(2, 0), sticky='nw')

        self.AnimalButton.bind("<<ComboboxSelected>>", self.Select_animal)

        # Select Day
        self.day_var = StringVar()
        Label(self.CohortButtonFrame, text='Select Day', style='EntryStyle.TLabel').grid(row=6, column=0,
                                                                                       padx=(5, 2),
                                                                                       pady=(5, 0))
        self.DayButton = Combobox(self.CohortButtonFrame, width=15, textvariable=self.day_var, values=[],
                                     postcommand=lambda: self.DayButton.config(values=self.drop_day()),
                                     exportselection=0,
                                     state='disabled', style="Btt.TCombobox", justify=CENTER,
                                     font=('Myriad', 12, 'bold'))
        self.DayButton.grid(row=7, column=0, padx=(2, 5), pady=(2, 0), sticky='nw')

        self.DayButton.bind("<<ComboboxSelected>>", self.Select_day)

        # AddRows
        self.addRowsButton = Button(TableButtonFrame, text="Add Rows", style="SideFrameButton.Btt.TButton",
                                    command=lambda: self.table_addRows())
        self.addRowsButton.grid(row=0, column=0, sticky='nsew', pady=5, padx=5)

        # DeleteRows
        self.delRowsButton = Button(TableButtonFrame, text="Delete Rows", style="SideFrameButton.Btt.TButton",
                                    command=lambda: self.table_deleteRows())
        self.delRowsButton.grid(row=0, column=1, columnspan=2, sticky='news', pady=5, padx=5)

        # Resize
        self.ResizeButton = Button(TableButtonFrame, text="Resize", style="SideFrameButton.Btt.TButton",
                                   command=lambda: self.table.autoResizeColumns())
        self.ResizeButton.grid(row=1, column=0, sticky='nsew', padx=5)

        # Clear Button
        self.ClearButton = Button(TableButtonFrame, text="Clear All", style="SideFrameButton.Btt.TButton",
                                  command=lambda: self.Clear_Table())
        self.ClearButton.grid(row=1, column=1, sticky='nsew')

        # Save Button
        self.SaveButton = Button(TableButtonFrame, text="Save", style="SideFrameButton.Btt.TButton",
                                 command=lambda: self.Save_cohort())
        self.SaveButton.grid(row=1, column=2, padx=5, sticky='nsew')

        self.ButtonList = [self.addRowsButton, self.delRowsButton, self.ResizeButton, self.ClearButton, self.SaveButton]

    def Load_cohort(self, cohort):

        try:
            with open(dir_path + '\\Cohort_data\\' + cohort + '.pickle', 'rb') as handle:
                self.full_data = pickle.load(handle)
            self.cohort_data = self.full_data['cohort']
            self.curr_cohort = cohort
            self.cohort_var.set(self.curr_cohort)
            self.config_file["Cohort Data"]['last cohort'] = self.curr_cohort
            with open('config.ini', 'w') as conf:
                self.config_file.write(conf)

        except:
            with open(dir_path + '\\Cohort_data\\' + self.cohort_list[0] + '.pickle', 'rb') as handle:
                self.full_data = pickle.load(handle)
            self.cohort_data = self.full_data['cohort']
            self.curr_cohort = self.cohort_list[0]
            self.cohort_var.set(self.curr_cohort)
            self.config_file["Cohort Data"]['last cohort'] = self.cohort_list[0]
            with open('config.ini', 'w') as conf:
                self.config_file.write(conf)
            self.text_area.insert(INSERT,
                                  f'\n{self.curr_cohort} couldn"t be opened, opening {self.cohort_list[0]} instead!')
            self.text_area.yview(END)

    def New_cohort(self, default=''):

        if default == '':
            name = simpledialog.askstring("New cohort name?", "ID:", initialvalue='', parent=self.root)
        else:
            name = default
        if name:
            new_cohort = {'cohort': {1: self.Cohort_dict_template}}

            with open(dir_path + f'\\Cohort_data\\{name}.pickle', 'wb') as handle:
                pickle.dump(new_cohort, handle, protocol=pickle.HIGHEST_PROTOCOL)
            self.Config_Cohort(name)
            self.animal_var.set('')

        else:
            return

    def Delete_cohort(self):

        delete_conf = messagebox.askquestion('Delete Cohort', 'Are you sure you want to delete this cohort?',
                                             icon='warning', parent=self.root)

        if delete_conf == 'yes':
            if len(self.cohort_list) == 1:
                os.remove(dir_path + '\\Cohort_data\\' + self.curr_cohort + '.pickle')
                self.New_cohort('eg_cohort')
                self.animal_var.set('')

            else:
                os.remove(dir_path + '\\Cohort_data\\' + self.curr_cohort + '.pickle')
                self.Config_Cohort(self.cohort_list[0])
                self.animal_var.set('')

        else:
            return

    def Rename_cohort(self):

        rename_conf = simpledialog.askstring('Rename', 'New cohort name?')

        rename("Cohort_data\\" + self.curr_cohort + ".pickle", "Cohort_data\\" + rename_conf + ".pickle")
        self.curr_cohort = rename_conf
        self.cohort_var.set(self.curr_cohort)


    def table_addRows(self, event=None):

        self.IDList = [self.full_data['cohort'][i]['Identifier'] for i in self.full_data['cohort']]
        num = simpledialog.askinteger("Now many rows?", "Number of rows:", initialvalue=1, parent=self.root)
        new_IDs_List = []
        self.tabletype = 'rows'
        self.table.getundo()
        for i in range(num):
            new_row_ID = str(max([int(i) for i in self.IDList]) + 1).zfill(4)
            new_IDs_List.append(new_row_ID)
            self.IDList.append(new_row_ID)
        for i in range(num):
            self.table.addRows(1, ID=new_IDs_List[i])
            self.table.redrawTable()

        self.tabletype = 'Cohort'



    def table_deleteRows(self):

        n = messagebox.askyesno("Delete",
                                "Delete This Record?",
                                parent=self.root)
        self.table.getundo()
        if n == True:
            IDRowList = list(self.full_data['cohort'].keys())
            if len(self.full_data['cohort']) > 1:
                if len(self.table.multiplerowlist) > 1:
                    pass
                    # for row in (self.table.multiplerowlist):
                    #     self.IDList.remove(self.full_data['cohort'][IDRowList[row]]['Identifier'])
                    #     self.full_data.pop(self.full_data['cohort'][IDRowList[row]]['Identifier'], None)
                    #     self.full_data['cohort'].pop(IDRowList[row])
                else:
                    row = self.table.getSelectedRow()
                    # self.IDList.remove(self.full_data['cohort'][IDRowList[row]]['Identifier'])
                    # self.full_data.pop(self.full_data['cohort'][IDRowList[row]]['Identifier'], None)
                    # self.full_data['cohort'].pop(IDRowList[row])

                self.table.deleteRow(confirm=1)

            else:
                #self.table.model.data[1] = self.Cohort_dict_template
                self.table.redrawTable()



    def Select_cohort(self, event):

        for widget in self.TableFrame.winfo_children():
            widget.destroy()

        self.Config_Cohort(self.SelectButton.get())

        self.animal_var.set('')
        self.tabletype = 'Cohort'

    def Save_cohort(self):

        if self.tabletype == 'Cohort':
            save_data = self.table.model.data
            IDCompare = len(self.full_data) - 1

            self.full_data['cohort'] = save_data

            IdentifierList = [self.full_data['cohort'][i]['Identifier'] for i in self.full_data['cohort']]

            IDRowList = list(self.full_data['cohort'].keys())

            if len(self.full_data['cohort']) > IDCompare:
                difIdentifiers = list(set(IdentifierList).difference(
                    set([i for i in self.full_data if i != ('cohort')])))
                difIdentifiers = natsorted(difIdentifiers)
                for i in range(len(difIdentifiers)):
                    self.full_data[difIdentifiers[i]] = {
                        self.full_data['cohort'][IDRowList[i + IDCompare]]['ID']: {1: self.Animal_dict_template}, '1': {1: self.Day_dict_template}}

            AnimalList =  []
            for i in range(self.table.model.getRowCount()):
                AnimalList.append(self.table.model.getValueAt(i,0))

            for i in range(len(IdentifierList)):

                if AnimalList[i] != self.full_data['cohort'][IDRowList[i]]['ID']:
                    print(self.full_data[IdentifierList[i]])
                    self.full_data[IdentifierList[i]] = {
                        self.full_data['cohort'][IDRowList[i]]['ID']: self.full_data[IdentifierList[i]].pop(
                            AnimalList[i]), '1': {1: self.Day_dict_template}}

            if IDRowList != [i + 1 for i in range(len(IDRowList))]:
                for i in range(len(IDRowList)):
                    self.full_data['cohort'][i + 1] = self.full_data['cohort'].pop(IDRowList[i])

            with open(dir_path + '\\Cohort_data\\' + self.curr_cohort + '.pickle', 'wb') as handle:
                pickle.dump(self.full_data, handle, protocol=pickle.HIGHEST_PROTOCOL)

            self.Load_cohort(self.curr_cohort)
            self.table.redrawTable()

            self.text_area.insert(INSERT, f'\nCohort Data saved to {self.curr_cohort}.pickle!')
            self.text_area.yview(END)

    def drop_animal(self, default=0):

        if default == 0:
            animal_data = [list(self.full_data[i].keys())[0] for i in self.full_data if i != 'cohort']
            return animal_data
        else:
            self.Load_cohort(default)
            animal_data = [list(self.full_data[i].keys())[0] for i in self.full_data if i != 'cohort']
            return animal_data

    def Select_animal(self, event, default=0):

        if default == 0:
            curr_animal_ID = self.AnimalButton.get()

            IDRowList = list(self.full_data['cohort'].keys())
            self.curr_animal_data = self.full_data[self.full_data["cohort"][IDRowList[self.AnimalButton.current()]]["Identifier"]][curr_animal_ID]

            for widget in self.TableFrame.winfo_children():
                widget.destroy()

            self.table = TableCanvas(self.TableFrame,
                                     cellwidth=100, cellbackgr='#FFFFFF',
                                     thefont=('Arial', 12), rowheight=25, rowheaderwidth=0,
                                     selectedcolor="#C8C8C8", multipleselectioncolor="#C8C8C8",
                                     rowselectedcolor='#C8C8C8', read_only=True, data=self.curr_animal_data)
            self.table.show()

            self.animal_var.set(curr_animal_ID)
            self.day_var.set('')

            for i in self.ButtonList:
                i.config(state='disabled')
            self.DayButton.config(state='readonly')
            
            # Progress Animal Button

            self.ProgressButton = Button(self.CohortButtonFrame, text="Progress\n  Animal", style="SideFrameButton.Btt.TButton",
                                       command=lambda: self.Progress_Animal())

            self.ProgressButton.grid(row=7, column=0, padx=(2, 5), pady=(0, 10), sticky='we')

        else:

            Animal = self.TrialAnimalButton
            IdentifierList = [self.full_data['cohort'][i]['Identifier'] for i in self.full_data['cohort']]
            AnimalTag = self.full_data[IdentifierList[Animal.current()]][Animal.get()]
            Row = list(AnimalTag.keys())[-1]
            IsEmpty = AnimalTag[Row]['Total Trials']

            if len(AnimalTag.keys()) == 1:
                Curr_day = '0'
                Curr_type = 'None'
                Next_day = AnimalTag[Row]['Day']
                Next_type = AnimalTag[Row]['Trial Type']
            elif IsEmpty == '':
                Curr_day = AnimalTag[Row-1]['Day']
                Curr_type = AnimalTag[Row-1]['Trial Type']
                Next_day = AnimalTag[Row]['Day']
                Next_type = AnimalTag[Row]['Trial Type']
            else:
                Curr_day = AnimalTag[Row]['Day']
                Curr_type = AnimalTag[Row]['Trial Type']
                Next_day = str(int(Curr_day) + 1)
                Next_type = Curr_type

            for i,f in zip(self.DayTypeList,[Curr_type,Curr_day,Next_type,Next_day]):
                i.config(state='enabled')
                i.delete(0,'end')
                i.insert(0, f)
                i.config(state='readonly')
            self.RunButton.config(state='enabled')


    def Progress_Animal(self):

        Animal = self.AnimalButton
        IdentifierList = [self.full_data['cohort'][i]['Identifier'] for i in self.full_data['cohort']]
        AnimalTag = self.full_data[IdentifierList[Animal.current()]][Animal.get()]
        Row = list(AnimalTag.keys())[-1]
        Day = AnimalTag[Row]
        TotalTrials = Day['Total Trials']

        if TotalTrials == '':
            self.text_area.insert(INSERT, "\nAnimal has yet to complete this stage!")
            self.text_area.yview(END)
            return
        else:
            CorrectTrials = int(Day['Correct'])
            FailedTrials = int(Day['Fail'])
            OmitedTrials = int(Day['Omissions'])
            MeanScore = round(CorrectTrials/int(TotalTrials),2)*100
            Accuracy = round(CorrectTrials/(CorrectTrials+FailedTrials),2)*100
            Omissions = round(OmitedTrials/int(TotalTrials),2)*100

        progress_conf = messagebox.askquestion('Progress Animal', f'Are you sure you want to progress this\n'
                                                                  f'animal to the next stage?\n'
                                                                  f'Mean Score = {MeanScore}%   (>60%)\n'
                                                                  f'Accuracy = {Accuracy}%   (>80%)\n'
                                                                  f'Omissions = {Omissions}%   (<30%)',
                                             icon='warning', parent=self.root)


        if progress_conf == 'yes':

            AnimalIdentifier = IdentifierList[self.AnimalButton.current()]
            IDList = list(self.full_data['cohort'].keys())
            AnimalID = self.full_data['cohort'][IDList[self.AnimalButton.current()]]['ID']
            LastDay = list(self.full_data[AnimalIdentifier][AnimalID].keys())[-1]
            LastType = self.full_data[AnimalIdentifier][AnimalID][LastDay]['Trial Type']
            TypeList = ['Habituation','Train1','Train2','Test']

            if LastType == 'Test':
                self.text_area.insert(INSERT, "\nCan't progress any further!")
                self.text_area.yview(END)
                return
            else:
                NewType = TypeList[TypeList.index(LastType)+1]
                self.full_data[AnimalIdentifier][AnimalID][LastDay+1] = self.Animal_dict_template

                self.full_data[AnimalIdentifier][AnimalID][LastDay+1]['Day'] = str(LastDay+1)

                self.full_data[AnimalIdentifier][AnimalID][LastDay+1]['Trial Type'] = NewType

                with open(dir_path + '\\Cohort_data\\' + self.curr_cohort + '.pickle', 'wb') as handle:
                    pickle.dump(self.full_data, handle, protocol=pickle.HIGHEST_PROTOCOL)

                with open(dir_path + '\\Cohort_data\\' + self.curr_cohort + '.pickle', 'rb') as handle:
                    self.full_data = pickle.load(handle)

                self.Select_animal('')
        else:
            return

    def drop_day(self):

        IdentifierList = [self.full_data['cohort'][i]['Identifier'] for i in self.full_data['cohort']]
        curr_Identifier = IdentifierList[self.AnimalButton.current()]
        day_list = list(self.full_data[curr_Identifier].keys())[1:]
        day_list = ['Day ' + i for i in day_list]
        return day_list

    def Select_day(self, event):

        IdentifierList = [self.full_data['cohort'][i]['Identifier'] for i in self.full_data['cohort']]
        curr_Identifier = IdentifierList[self.AnimalButton.current()]
        curr_day = self.DayButton.get().replace('Day ','')
        self.day_data = self.full_data[curr_Identifier][curr_day]


        for widget in self.TableFrame.winfo_children():
            widget.destroy()

        self.table = TableCanvas(self.TableFrame,
                                 cellwidth=150, cellbackgr='#FFFFFF',
                                 thefont=('Arial', 12), rowheight=25, rowheaderwidth=0,
                                 selectedcolor="#C8C8C8", multipleselectioncolor="#C8C8C8",
                                 rowselectedcolor='#C8C8C8', read_only=True, data=self.day_data)
        self.table.show()

        self.day_var.set('Day ' + curr_day)

        for i in self.ButtonList:
            i.config(state='disabled')

    def Clear_Table(self):
        mul = [[i for i in range(0, self.table.model.getRowCount())],
               [i for i in range(0, self.table.model.getColumnCount())]]
        for col in mul[1]:
            for row in mul[0]:
                if col != mul[1][-1]:
                    self.table.model.setValueAt('', row, col)  ##use cell coords
                    self.table.redrawTable()
        self.text_area.insert(INSERT, '\nData cleared')
        self.text_area.yview(END)

    def Trial_Config(self):

        for widget in self.mainFrame.winfo_children():
            widget.destroy()

        def test_Val_Trial(inStr, acttyp):  # Function to validate Entry widget input as digits
            if acttyp == '1':
                if not inStr.isdigit():
                    return False
                elif int(inStr) > 99:
                    return False
            return True

        vcmdTrial = self.mainFrame.register(test_Val_Trial), '%P', '%d'  # Command to check if input is digits

        self.mainFrameLabel.config(text='5-CSRTT', padding=[0, 5, 0, 15])

        typeFrame = Frame(self.mainFrame, style="EntryFrameStyle.TFrame")
        typeFrame.grid(row=0, column=1, pady=(0, 5), sticky='nswe')

        # Curr Cohort
        CohortFrame = Frame(self.mainFrame, style="EntryFrameStyle.TFrame")
        CohortFrame.grid(row=0, column=0, pady=(0, 5), padx=7, sticky='nswe')

        Label(CohortFrame, text='Select Cohort', style='EntryStyle.TLabel').grid(row=0, column=0, padx=(5, 2),
                                                                                 pady=(5, 0))
        self.TrialCohortButton = Combobox(CohortFrame, width=15, textvariable=self.cohort_var,
                                          values=natsorted(self.cohort_list),
                                          exportselection=0,
                                          state='readonly', style="Btt.TCombobox", justify=CENTER,
                                          font=('Myriad', 12, 'bold'))
        self.TrialCohortButton.grid(row=1, column=0, padx=(5, 5), pady=(5, 5), sticky='nw')


        # Curr Animal
        Label(CohortFrame, text='Select animal', style='EntryStyle.TLabel').grid(row=2, column=0, padx=(5, 2),
                                                                                 pady=(5, 0))
        TrialAnimal_var = StringVar()
        self.TrialAnimalButton = Combobox(CohortFrame, width=15, values=[], text=TrialAnimal_var,
                                          postcommand=lambda: self.TrialAnimalButton.config(
                                              values=self.drop_animal(self.TrialCohortButton.get())), exportselection=0,
                                          state='readonly', style="Btt.TCombobox", justify=CENTER,
                                          font=('Myriad', 12, 'bold'))
        self.TrialAnimalButton.grid(row=3, column=0, padx=(5, 5), pady=(5, 5), sticky='nw')
        self.TrialAnimalButton.bind("<<ComboboxSelected>>", lambda x: self.Select_animal('', default=1))

        trialtypelabel = Label(typeFrame, text='Last trial:', style='EntryStyle.TLabel', font=('Myriad', 12))
        trialtypelabel.grid(row=0, column=0, columnspan=4, pady=(5, 3), padx=5)

        Label(typeFrame, text='Type:', style='EntryStyle.TLabel').grid(row=1, column=0, padx=(5, 5))

        self.Now_Type = Entry(typeFrame, exportselection=0, font=('Myriad', 12), cursor='xterm', width=10, justify='center',
                          state='readonly')
        self.Now_Type.grid(row=1, column=1, padx=(0, 5))
        self.Now_Type.insert(0, '')

        Label(typeFrame, text='Day:', style='EntryStyle.TLabel').grid(row=1, column=2, padx=(5, 5), pady=(5, 5))
        self.Now_Day = Entry(typeFrame, exportselection=0, font=('Myriad', 12), cursor='xterm', width=3, justify='center',
                         state='readonly')
        self.Now_Day.grid(row=1, column=3, padx=(0, 5))
        self.Now_Day.insert(0, '')

        trialtypelabel = Label(typeFrame, text='Next trial:', style='EntryStyle.TLabel', font=('Myriad', 12))
        trialtypelabel.grid(row=2, column=0, columnspan=4, pady=(5, 3), padx=5)
        Label(typeFrame, text='Type:', style='EntryStyle.TLabel').grid(row=3, column=0, padx=(5, 5), pady=(0, 5))
        self.Then_Type = Entry(typeFrame, exportselection=0, font=('Myriad', 12), cursor='xterm', width=10, justify='center',
                          state='readonly')
        self.Then_Type.grid(row=3, column=1, padx=(0, 5), pady=(0, 5))
        self.Then_Type.insert(0, '')
        Label(typeFrame, text='Day:', style='EntryStyle.TLabel').grid(row=3, column=2, padx=(5, 5), pady=(5, 5))
        self.Then_Day = Entry(typeFrame, exportselection=0, font=('Myriad', 12), cursor='xterm', width=3, justify='center',
                         state='readonly')
        self.Then_Day.grid(row=3, column=3, padx=(0, 5), pady=(0, 5))
        self.Then_Day.insert(0, '')

        self.DayTypeList = [self.Now_Type, self.Now_Day, self.Then_Type, self.Then_Day]
        self.TrialCohortButton.bind("<<ComboboxSelected>>",
                                    lambda x: [[i.config(state='enabled') for i in self.DayTypeList],
                                               [i.delete(0,'end') for i in self.DayTypeList],
                                               [i.config(state='readonly') for i in self.DayTypeList],
                                               TrialAnimal_var.set(''), self.RunButton.config(state='disabled')])

        # Trial Settings
        trialFrame = Frame(self.mainFrame, style="EntryFrameStyle.TFrame")
        trialFrame.grid(row=0, column=2, padx=10, pady=(0, 5), sticky='wnes')

        TDurL = Label(trialFrame, text='TD:', style='EntryStyle.TLabel')
        TDurL.grid(row=1, column=1, padx=(5, 5), pady=(15, 5))
        self.TDur = Entry(trialFrame, exportselection=0, font=('Myriad', 12), cursor='xterm', width=3, justify='center',
                          validate='key',
                          validatecommand=vcmdTrial)
        self.TDur.grid(row=1, column=2, padx=(0, 5), pady=(15, 5))
        self.TDur.insert(0, self.tdur)

        TDur_TTip = CreateToolTip(TDurL, "Trial duration (min):\nTotal duration of the whole 5-CSRTT routine")

        CritL = Label(trialFrame, text='Crit:', style='EntryStyle.TLabel')
        CritL.grid(row=2, column=1, padx=(5, 5), pady=(5, 5))

        self.Crit = Entry(trialFrame, exportselection=0, font=('Myriad', 12), cursor='xterm', width=3, justify='center',
                          validate='key',
                          validatecommand=vcmdTrial)
        self.Crit.grid(row=2, column=2, padx=(0, 7), pady=(5, 5))
        self.Crit.insert(0, self.crit)

        Crti_TTip = CreateToolTip(CritL, "Criterion:\nNumber of correct trials required to proceed")

        ItiL = Label(trialFrame, text='ITI:', style='EntryStyle.TLabel')
        ItiL.grid(row=3, column=1, padx=(5, 5),
                  pady=(5, 5))
        self.Iti = Entry(trialFrame, exportselection=0, font=('Myriad', 12), cursor='xterm', width=3, justify='center',
                         validate='key',
                         validatecommand=vcmdTrial)
        self.Iti.grid(row=3, column=2, padx=(0, 5), pady=(5, 5))
        self.Iti.insert(0, self.ITI)

        Iti_TTip = CreateToolTip(ItiL, "Inter-trial Interval (s):\nWait time after each correct nosepoke")

        SdL = Label(trialFrame, text='SD:', style='EntryStyle.TLabel')
        SdL.grid(row=1, column=3, padx=(5, 5), pady=(15, 5))
        self.Sd = Entry(trialFrame, exportselection=0, font=('Myriad', 12), cursor='xterm', width=3, justify='center',
                        validate='key',
                        validatecommand=vcmdTrial)
        self.Sd.grid(row=1, column=4, padx=(0, 10), pady=(15, 5))
        self.Sd.insert(0, self.SD)

        Sd_TTip = CreateToolTip(SdL, "Stimulus duration (s):\nTime each hole light is on for stimulus presentation")

        LhL = Label(trialFrame, text='LH:', style='EntryStyle.TLabel')
        LhL.grid(row=2, column=3, padx=(5, 5), pady=(5, 5))
        self.Lh = Entry(trialFrame, exportselection=0, font=('Myriad', 12), cursor='xterm', width=3, justify='center',
                        validate='key',
                        validatecommand=vcmdTrial)
        self.Lh.grid(row=2, column=4, padx=(0, 5), pady=(5, 5))
        self.Lh.insert(0, self.LH)

        Lh_TTip = CreateToolTip(LhL,
                                "Limited Hold (s):\nTime the animal has to interact with the correct hole\nafter stimulus presentation")

        ToL = Label(trialFrame, text='TO:', style='EntryStyle.TLabel')
        ToL.grid(row=3, column=3, padx=(5, 5), pady=(5, 5))
        self.To = Entry(trialFrame, exportselection=0, font=('Myriad', 12), cursor='xterm', width=3, justify='center',
                        validate='key',
                        validatecommand=vcmdTrial)
        self.To.grid(row=3, column=4, padx=(0, 5), pady=(5, 5))
        self.To.insert(0, self.LH)

        To_TTip = CreateToolTip(ToL,
                                "Time out (s):\nTime the animal has wait with the lights out\nafter making a mistake")

        TrialSetList = []

        # Load Default Settings Button
        self.LoadSetButton = Button(self.mainFrame, text="Load Defaults", style="SideFrameButton.Btt.TButton",
                                    command=lambda: self.Load_Trial_Set())
        self.LoadSetButton.grid(row=1, column=2, pady=5, sticky='n')

        # Save Button
        self.SaveButton = Button(self.mainFrame, text="Save", style="SideFrameButton.Btt.TButton",
                                 command=lambda: self.Save_Trial_Config())
        self.SaveButton.grid(row=2, column=0, padx=(7, 0), pady=5, sticky='s')

        # Run Button
        self.RunButton = Button(self.mainFrame, text="Run", style="SideFrameButton.Btt.TButton", state='disabled',
                                command=lambda: [self.FCSRTT_Run(), self.KillButton.config(state='enabled')])
        self.RunButton.grid(row=2, column=1, pady=5, sticky='s')

        # Kill Button
        self.KillButton = Button(self.mainFrame, text="Kill", style="SideFrameButton.Btt.TButton",
                                 command=lambda: self.FCSRTT_Terminate(), state='disabled')
        self.KillButton.grid(row=2, column=2, pady=5, sticky='s')

    def Load_Trial_Set(self):
        type = self.TrialAnimalButton.get()
        TrialSetList = [self.TDur, self.Crit, self.Iti, self.Sd, self.Lh, self.To]
        HabSet = [30, 50, 5, 30, 30, 0] # TD/Crit/ITI/SD/LH/TO
        TrainSet1 = [30,50,5,30,30,5]
        TrainSet2 = [30,50,5,15,15,5]

        if type == 'Habituation':
            for i, f in zip(TrialSetList, HabSet):
                i.config(validate='none')
                i.delete(0, 'end')
                i.insert(0, f)
                i.config(validate='key')

        if type == 'Train 1':
            for i, f in zip(TrialSetList, TrainSet1):
                i.config(validate='none')
                i.delete(0, 'end')
                i.insert(0, f)
                i.config(validate='key')

        if type == 'Train 2':
            for i, f in zip(TrialSetList, TrainSet2):
                i.config(validate='none')
                i.delete(0, 'end')
                i.insert(0, f)
                i.config(validate='key')



    def Save_Trial_Config(self):

        self.Trial['trial type'] = self.Then_Type.get()

        self.Trial['trial duration'] = self.TDur.get()
        self.Trial['criterion'] = self.Crit.get()
        self.Trial['iti'] = self.Iti.get()
        self.Trial['to'] = self.To.get()
        self.Trial['lh'] = self.Lh.get()
        self.Trial['sd'] = self.Sd.get()

        self.config_file["Cohort Data"]['last cohort'] = self.TrialCohortButton.get()

        with open('config.ini', 'w') as conf:
            self.config_file.write(conf)

        self.curr_cohort = self.TrialCohortButton.get()
        self.config_file.read("config.ini")
        self.read_config()

        self.text_area.insert(INSERT, '\nTrial settings saved!')
        self.text_area.yview(END)


    def FCSRTT_Run(self):

        self.Save_Trial_Config()

        def text_area_update():

            while True:
                val = self.text_area_val.get()
                if val == 'break':
                    break
                else:
                    self.text_area.insert(INSERT, '\n' + val)
                    self.text_area.yview(END)

        self.text_area_val = Queue()
        self.text_area_thread = threading.Thread(target=text_area_update)

        IO_Val = [self.in1, self.in2, self.in3, self.in4,
                  self.ser, self.rclk, self.srclk,
                  self.IREm, self.IR1, self.IR2, self.IR3, self.IR4, self.IR5,
                  self.LK, self.LGTNo, self.NSR,
                  self.HL1, self.HL2, self.HL3, self.HL4, self.HL5, self.AmbL1, self.AmbL2, self.AmbL3, self.AmbL4, self.RWLi,
                  ]

        Trial_Val = [self.ttyp, self.tdur, self.crit, self.ITI, self.TO, self.LH, self.SD]

        values_to_pass = [IO_Val, Trial_Val, self.text_area_val]

        try:
            global testing
            self.text_area_thread.start()
            self.text_area.insert(INSERT, '\nInitiating Inator!...')
            self.text_area.yview(END)
            for w in self.sideFrame.winfo_children():
                if 'button' in w.winfo_name():
                    w['state'] = 'disabled'
            for w in self.mainFrame.winfo_children():
                if 'button' in w.winfo_name():
                    w['state'] = 'disabled'
            event = Event()
            testing = Process(target=FCSRTT, args=(values_to_pass,event))
            ## TODO: Config this properly
            testing.start()

            self.KillButton.config(state='enable')

        except:
            print('Something went horribly wrong!')
            self.text_area.insert(INSERT, '\nSomething went horribly wrong!')
            self.text_area.yview(END)
            for w in self.sideFrame.winfo_children():
                if 'button' in w.winfo_name():
                    w['state'] = "enabled"
            self.KillButton.config(state='disabled')

    def FCSRTT_Terminate(self):

        self.text_area.insert(INSERT, '\nTerminating...')
        self.text_area.yview(END)

        try:
            testing.terminate()
            self.text_area_val.put('break')
            self.text_area_thread.join()
            for w in self.sideFrame.winfo_children():
                if 'button' in w.winfo_name():
                    w['state'] = 'enabled'
            for w in self.mainFrame.winfo_children():
                if 'button' in w.winfo_name():
                    w['state'] = 'enabled'
            self.KillButton.config(state='disabled')
            self.text_area.insert(INSERT, '\nInator destroyed!')
            self.text_area.yview(END)
        except:
            self.text_area.insert(INSERT, '\nIt''s too powerful to destroy!')
            self.text_area.yview(END)
            self.KillButton.config(state='disabled')


def main():
    master = Tk()
    Inator(master)
    master.mainloop()


if __name__ == "__main__":
    main()


    # TODO: Create project loading capability

    # TODO: Clear up code
    # TODO: Clear up import *
    # TODO: Comment everything

    # TODO: Make changes in script to record: premature responses, repetition errors, responses during TO