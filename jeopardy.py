import shelve
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
import sys
import os
import serial
from serial.tools import list_ports

ports = list_ports.comports()
if len(ports) == 0 or os.environ.get("NO_SERIAL_PORTS", "0") == "1":
    # no ports or diabled by ENV
    print("No serial ports found!")
    # exit(1)
    ser = None
else:
    port = None
    if len(ports) > 1:
        for i, port in enumerate(ports):
            print(f"{i}: {port.device} - {port.description}")
        choice = int(input("Select port (0-{}): ".format(len(ports)-1)))
        if choice < 0 or choice >= len(ports):
            port = ports[choice]
    else:
        port = ports[0]
    if port is None:
        ser = None
    else:
        ser = serial.Serial(
            port=port.device,
            baudrate=9600,
            parity=serial.PARITY_ODD,
            stopbits=serial.STOPBITS_TWO,
            bytesize=serial.SEVENBITS
        )
        

question_dir = os.path.join(".", "questions")

teams = shelve.open("teams.db", writeback=True)
for i in range(4):
    teamkey = f"team{i}"
    if teamkey in teams:
        # team already exists
        continue
    teams[teamkey] = {
        "name": f"Team {i}",
    }
    
point_dict = shelve.open("points.db", writeback=True)
additional_points = shelve.open("additional_points.db", writeback=True)

categories = sorted(os.listdir(question_dir))
question_file = {} # category -> points -> filename
for category in categories:
    question_file[category] = {}
    for filename in os.listdir(os.path.join(question_dir, category)):
        if "disabled" in filename:
            continue
        points = int(filename.split(".")[0])
        question_file[category][points] = filename
            
score_buttons = {}
point_buttons = {}
mainWindow : "MainWindow | None" = None

def recompute_scores():
    scores = {}
    for team in teams:
        scores[team] = 0
    for category, data in point_dict.items():
        for score, teamdata in data.items():
            for team, score in teamdata:
                if team not in scores:
                    print(f"Invalid team {team} in for category {category} and score {score}")
                    continue
                scores[team] += score
                
    for team, deltas in additional_points.items():
        for delta in deltas:
            if team not in scores:
                print(f"Invalid team {team} in additional points")
                continue
            scores[team] += delta
            
    for team, score in scores.items():
        if team not in score_buttons:
            print(f"Invalid team {team} in score buttons")
            continue
        score_buttons[team].setText(str(score))
        teams[team].update({"score": score})
        

class QuestionWindow(QWidget):
    def __init__(self, category, score):
        super().__init__()
        print("Creating question window for", category, score)
        layout = QVBoxLayout()
        
        self.category = category
        self.score = score
        self.input = -1
        self.team_buttons = []
        
        filename = question_file[category][score]
        if filename.endswith(".txt"):
            with open(os.path.join(question_dir, category, filename), "r") as f:
                question = f.read()
            lbl = QLabel(question)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setWordWrap(True)
            layout.addWidget(lbl)
        else:
            print("image file", filename)
            img = QImage(os.path.join(question_dir, category, filename))
            img = img.scaled(800, 600, Qt.AspectRatioMode.KeepAspectRatio)
            lbl = QLabel()
            lbl.setPixmap(QPixmap(img))
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(lbl)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
        
        award_layout = QHBoxLayout()
        for team, data in sorted(teams.items(), key=lambda x: x[0]):
            button = QPushButton(f"Award {data['name']}")
            button.setStyleSheet("background-color: darkblue; color: yellow; font-size: 20px; font-weight: bold;")
            button.setIconSize(QSize(50, 50))
            button.setIcon(QIcon("P.png"))
             
            button.setMinimumHeight(75)
            button.setMinimumWidth(200)
            button.clicked.connect(lambda _, t=team, c=category, s=score: self.award_points(t, c, s))
            
            no_answer_btn = QPushButton(f"No Question")
            no_answer_btn.setStyleSheet("background-color: darkblue; color: yellow; font-size: 20px; font-weight: bold;")
            no_answer_btn.setMinimumHeight(25)
            no_answer_btn.setMinimumWidth(175)
            no_answer_btn.clicked.connect(lambda _, t=team, c=category, s=score: self.award_points(t, c, s, False))
            
            wrong_btn = QPushButton(f"X")
            wrong_btn.setStyleSheet("background-color: red; color: yellow; font-size: 20px; font-weight: bold;")
            wrong_btn.setMinimumHeight(25)
            wrong_btn.setMinimumWidth(25)
            wrong_btn.setMaximumWidth(25)
            wrong_btn.clicked.connect(lambda _, t=team, c=category, s=score: self.wrong_answer(t,c,s))
            
            extra_btn = QHBoxLayout()
            extra_btn.addWidget(no_answer_btn)
            extra_btn.addWidget(wrong_btn)
            extra_btn.setSpacing(0)
            
            button_layout = QVBoxLayout()
            button_layout.addWidget(button)
            button_layout.addLayout(extra_btn)
            button_layout.setSpacing(0)
            
            award_layout.addLayout(button_layout)
            self.team_buttons.append((button, (no_answer_btn,wrong_btn)))
            
        additional_layout = QVBoxLayout()
        close_button = QPushButton("Close")
        close_button.setStyleSheet("background-color: darkblue; color: yellow; font-size: 20px; font-weight: bold;")
        close_button.clicked.connect(self.on_close)
        close_button.setMinimumHeight(60)
        close_button.setMinimumWidth(200)
        
        reset_button = QPushButton("Reset")
        reset_button.setStyleSheet("background-color: darkblue; color: yellow; font-size: 20px; font-weight: bold;")
        reset_button.clicked.connect(self.reset_team_buttons)
        reset_button.setMinimumHeight(60)
        reset_button.setMinimumWidth(200)
        
        additional_layout.addWidget(close_button)
        additional_layout.addWidget(reset_button)
        additional_layout.setSpacing(0)
        
        additional_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        award_layout.addLayout(additional_layout)
            
        layout.addLayout(award_layout)
        self.setStyleSheet("background-color: white; color: black; font-size: 20px; font-weight: bold;")
        self.setLayout(layout)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setAttribute(Qt.WidgetAttribute.WA_AlwaysStackOnTop)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
        self.destroyed.connect(self.on_close)
        self.setWindowTitle(f"Question for {category} {score}")
        
        # poll serial port for team that buzzed in
        if ser is not None:
            print("Starting serial port polling")
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.poll_serial)
            self.timer.start(100)
        else:
            print("No serial port found, skipping polling")
            self.timer = None
        
    def reset_team_buttons(self):
        for button, _ in self.team_buttons:
            button.setStyleSheet("background-color: darkblue; color: yellow; font-size: 20px; font-weight: bold;")
        self.input = -1
            
    def poll_serial(self):
        assert ser is not None
        if self.input != -1:
            # read all data from serial port
            while ser.in_waiting > 0:
                ser.readline()
            return
        if ser.in_waiting > 0:
            data = ser.readline().decode("utf-8").strip()
            print("Received data:", data)
            index = int(data)
            if index < len(self.team_buttons):
                print("Team", index, "buzzed in")
                self.input = index
                team, _ = self.team_buttons[index]
                team.setStyleSheet("background-color: green; color: white; font-size: 20px; font-weight: bold;")
            else:
                print("Invalid team index", index)
        
        
    def on_close(self):
        print("Closing question window for", self.category, self.score)
        set_normal_button(self.category, self.score)
        if self.timer is not None:
            self.timer.stop()
        self.close()
        assert mainWindow is not None
        mainWindow.open_question = None
        
    def wrong_answer(self, team, category, score):
        print("Wrong answer for team", team)
        if team not in teams:
            print(f"Invalid team {team} in for category {category} and score {score}")
            return
        self.reset_team_buttons()
        # score = self.score
        if category not in point_dict:
            point_dict[category] = {}
        if score not in point_dict[category]:
            point_dict[category][score] = []
        point_dict[category][score].append((team, -score))
        recompute_scores()
        point_dict.sync()
        
        
    def award_points(self, team, category, score, full_points=True):
        if team not in teams:
            print(f"Invalid team {team} in for category {category} and score {score}")
            return
        if category not in point_dict:
            point_dict[category] = {}
        if score not in point_dict[category]:
            point_dict[category][score] = []
        # else:
        #     print(f"Score {score} already awarded for category {category}")
        if self.timer is not None:
            self.timer.stop()
        point_dict[category][score].append((team, score if full_points else score // 2))
        disable_button(category, score)
        recompute_scores()
        point_dict.sync()
        self.close()
        assert mainWindow is not None
        assert mainWindow.open_question is not None
        mainWindow.open_question = None
        
        
def select_point(category, score):
    global mainWindow
    if mainWindow is None:
        return
    assert mainWindow is not None
    if mainWindow.open_question:
        print("A question is already open")
        return
    print(f"Selected point {category} {score}")
    set_active_button(category, score)
    
    question_window = QuestionWindow(category, score)
    
    mainWindow.open_question = (question_window, category, score)
    mainWindow.open_question[0].show()
    
def disable_button(category, score):
    if category not in point_buttons or score not in point_buttons[category]:
        print(f"Button for {category} {score} not found")
        return
    button = point_buttons[category][score]
    button.setDisabled(True)
    
    team_scores = {}
    # for team, _ in teams.items():
    #     team_scores[team] = 0
    winner = None
    losers = []
    for team, score in point_dict[category][score]:
        if team not in team_scores:
            team_scores[team] = 0
        team_scores[team] += score
        if score > 0:
            winner = (team, score)
        elif score < 0:
            losers.append(team)
    button.setStyleSheet("background-color: gray; color: white; font-size: 15px; font-weight: bold;")
    button.setIconSize(QSize(0, 0))
    # losers = [teams[team]["name"] for team in sorted(team_scores.keys()) if team_scores[team] < 0]
    loser_txt = "\n"
    for i, team in enumerate(sorted(losers)):
        if i > 0:
            loser_txt += ", " 
        if i > 0 and i%2 == 0:
            loser_txt += "\n"
        loser_txt += teams[team]["name"]
            
    button.setText(
        ((teams[winner[0]]["name"] + " (+" + str(winner[1]) + ")\n") if winner else "")+
        loser_txt
    )
    # txt =  (
    #     ((teams[winner[0]]["name"] + " (+" + str(winner[1]) + ")") if winner else "")+
    #     # +", ".join([str(team_scores[team]) for team in sorted(team_scores.keys())])
    #     ", ".join([teams[team]["name"] for team in sorted(team_scores.keys()) if team_scores[team] < 0])
    # )
    # lbl = QLabel(txt,button)
    # lbl.setWordWrap(True)
    # lbl.setStyleSheet("color: white; font-size: 15px; font-weight: bold;")
    # # lbl.setMinimumWidth(button.width())
    # # lbl.setMaximumWidth(button.width())
    # # lbl.setMinimumHeight(button.height())
    # # lbl.setMaximumHeight(button.height())
    # lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    
    # allow word wrap
    # button.setWordWrap(True)
        
    # winners = len([team for team in team_scores if team_scores[team] > 0])
    # if winners == 0:
    #     button.setText("---")
    # elif winners == 1:
    #     team = [team for team in team_scores if team_scores[team] > 0][0]
    #     button.setText(teams[team]["name"]+f" (+{team_scores[team]})")
    # else:
    #     print("Multiple winners for category", category, "and score", score)
        
    # score_text = ", ".join([str(score) for _, score in sorted(team_scores.items(), key=lambda x: x[0])])
    # button.setText(score_text)
    
    # team,full_points = point_dict[category][score]
    # if team not in teams:
    #     print(f"Invalid team {team} in for category {category} and score {score}")
    #     return
    # awarded_score = score if full_points else score // 2
    # button.setText(teams[team]["name"]+f" (+{awarded_score})")
    
def set_active_button(category, score):
    if category not in point_buttons or score not in point_buttons[category]:
        print(f"Button for {category} {score} not found")
        return
    button = point_buttons[category][score]
    button.setDisabled(False)
    button.setStyleSheet("background-color: blue; color: yellow; font-size: 20px; font-weight: bold;")
    
def set_normal_button(category, score):
    if category not in point_buttons or score not in point_buttons[category]:
        print(f"Button for {category} {score} not found")
        return
    button = point_buttons[category][score]
    button.setDisabled(False)
    button.setStyleSheet("background-color: darkblue; color: yellow; font-size: 20px; font-weight: bold;")
    button.setText(str(score))
    
    
def undo_point(category, score):
    if category not in point_dict:
        print(f"Category {category} not found")
        return
    if score not in point_dict[category]:
        print(f"Score {score} not found in category {category}")
        return
    # team, full_points = point_dict[category][score]
    # if team not in teams:
    #     print(f"Invalid team {team} in for category {category} and score {score}")
    #     return
    
    # only positive points
    # for team, awarded_score in point_dict[category][score]:
    #     if awarded_score < 0 and 0 in point_dict[category]:
    #         # move negative to 0 question
    #         point_dict[category][0].append((team, -awarded_score))
    del point_dict[category][score]
    set_normal_button(category, score)
    recompute_scores()
    point_dict.sync()
    

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.open_question : "None | tuple[QuestionWindow,str,int]" = None

        self.setWindowTitle("Jeopardy")

        # button yellow text, blue background
        # black background for the whole window
        
        icon = QIcon("P.png")
        
        vtbox = QVBoxLayout()
        hbox = QHBoxLayout()
        for category in categories:
            vbox = QVBoxLayout()
            lbl = QLabel(category)
            lbl.setStyleSheet("font-size: 20px; font-weight: bold; color: white; background-color: darkblue;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.mouseDoubleClickEvent = lambda event, c=category: select_point(c, 0)
            vbox.addWidget(lbl)
            point_buttons[category] = {}
            for score in sorted(question_file[category].keys()):
                if score == 0:
                    continue
                button = QPushButton(str(score))
                button.setIconSize(QSize(50, 50))
                button.setIcon(icon)
                button.setMinimumHeight(100)
                button.setMinimumWidth(200)
                point_buttons[category][score] = button
                set_normal_button(category, score)
                if category in point_dict and score in point_dict[category]:
                    disable_button(category, score)
                    button.setMinimumWidth(150)
                    button2 = QPushButton("X")
                    button2.setStyleSheet("background-color: darkgray; color: white; font-size: 20px; font-weight: bold;")
                    button2.setMinimumHeight(100)
                    button2.setMinimumWidth(50)
                    button2.setMaximumWidth(50)
                    button2.clicked.connect(lambda _, c=category, s=score: undo_point(c, s))
                    hgroup = QHBoxLayout()
                    hgroup.addWidget(button)
                    hgroup.addWidget(button2)
                    hgroup.setSpacing(0)
                    vbox.addLayout(hgroup)
                else:
                    vbox.addWidget(button)
                button.clicked.connect(lambda _, c=category, s=score: select_point(c, s))
                    
            hbox.addLayout(vbox)
            
        vtbox.addLayout(hbox)
        
        pointbox = QHBoxLayout()
        for team, data in sorted(teams.items(), key=lambda x: x[0]):
            vbox = QVBoxLayout()
            lbl = QLineEdit(data["name"])
            lbl.setStyleSheet("font-size: 20px; font-weight: bold; color: white; background-color: darkblue;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            # write back on change
            def update_team_name(new_name, team=team):
                print(f"Updating team {team} to {new_name}")
                teams[team].update({"name": new_name})
                teams.sync()
            lbl.textChanged.connect(lambda text, team=team: update_team_name(text, team))
            vbox.addWidget(lbl)
            button = QPushButton("0")
            button.setStyleSheet("background-color: darkblue; color: yellow; font-size: 20px; font-weight: bold;")
            button.setIconSize(QSize(50, 50))
            button.setIcon(icon)
            button.setMinimumHeight(100)
            button.setMinimumWidth(200)
            button.setContextMenuPolicy(Qt.CustomContextMenu)
            button.customContextMenuRequested.connect(lambda pos, team=team: self.adjust(team,-100))
            button.clicked.connect(lambda _, team=team: self.adjust(team, 100))
            score_buttons[team] = button
            vbox.addWidget(button)
            pointbox.addLayout(vbox)
        vtbox.addLayout(pointbox)
        recompute_scores()
        
        vbox = QVBoxLayout()
            
        root = QWidget()
        root.setStyleSheet("background-color: black;")
        root.setLayout(vtbox)
        
        self.setCentralWidget(root)
        self.show()
        
    def adjust(self, team, delta):
        if team not in teams:
            print(f"Invalid team {team}")
            return
        if team not in score_buttons:
            print(f"Invalid team {team} in score buttons")
            return
        if team not in additional_points:
            additional_points[team] = []
        additional_points[team].append(delta)
        additional_points.sync()
        recompute_scores()


app = QApplication(sys.argv)
mainWindow = MainWindow()
app.exec()