from tkinter import *
from tkinter import font
from random import randint
import json
import os

with open('parsed_sat_questions.json', 'r') as file:
    rawQuestions = json.load(file)
#print(json.dumps(data, indent=4))

w = Tk()
w.title('Prepster')
w.minsize(280, 285)

#vars
Information_and_Ideas, Craft_and_Structure, Expression_of_Ideas, Conventions = (
    BooleanVar(value=True), BooleanVar(value=True), BooleanVar(value=True), BooleanVar(value=True))
easy, med, hard = BooleanVar(value=True), BooleanVar(value=True), BooleanVar(value=True)

domain_flags = {
    "Information and Ideas": Information_and_Ideas,
    "Craft and Structure": Craft_and_Structure,
    "Expression of Ideas": Expression_of_Ideas,
    "Standard English Conventions": Conventions}
difficulty_flags = {
    "Easy": easy,
    "Medium": med,
    "Hard": hard}

#init stats
DOMAINS = domain_flags.keys()
DIFFICULTIES = difficulty_flags.keys()

domain_stats_last = {k: {"correct": 0, "total": 0} for k in DOMAINS}
difficulty_stats_last = {k: {"correct": 0, "total": 0} for k in DIFFICULTIES}
all_stats_last = {"correct": 0, "total": 0}
domain_times_last = {k: [] for k in DOMAINS}
difficulty_times_last = {k: [] for k in DIFFICULTIES}
all_times_last = []

domain_stats_alltime = {k: {"correct": 0, "total": 0} for k in DOMAINS}
difficulty_stats_alltime = {k: {"correct": 0, "total": 0} for k in DIFFICULTIES}
all_stats_alltime = {"correct": 0, "total": 0}
domain_times_alltime = {k: [] for k in DOMAINS}
difficulty_times_alltime = {k: [] for k in DIFFICULTIES}
all_times_alltime = []

qCompleted = []
print('qCompleted: ', qCompleted)

currentDom = None
currentDiff = None


cells = {}
numCorrect = 0
numIncorrect = 0
r = None
time = 1
tick = 0
timer_job = None
width = 1000

#updates data from previous sessions
go = True
if os.path.exists("user_data.json") and go:
    print("loading user data")
    with open("user_data.json") as f:
        stats = json.load(f)

    domain_times_last.update(stats["last"]["domain times"])
    difficulty_times_last.update(stats["last"]["difficulty times"])
    all_times_last[:] = stats["last"]["overall times"]
    domain_stats_last.update(stats["last"]["domain"])
    difficulty_stats_last.update(stats["last"]["difficulty"])
    all_stats_last.update(stats["last"]["overall"])

    domain_times_alltime.update(stats["alltime"]["domain times"])
    difficulty_times_alltime.update(stats["alltime"]["difficulty times"])
    all_times_alltime[:] = stats["alltime"]["overall times"]
    domain_stats_alltime.update(stats["alltime"]["domain"])
    difficulty_stats_alltime.update(stats["alltime"]["difficulty"])
    all_stats_alltime.update(stats["alltime"]["overall"])
    qCompleted[:] = stats["qCompleted"]
#funcs
def avg_times(times):
    return f'{round(sum(times) / len(times)) if times else "—"} Sec'

def clear_usrData():
    for stats_dict in (
        domain_stats_last,
        difficulty_stats_last,
        domain_stats_alltime,
        difficulty_stats_alltime,
    ):
        for v in stats_dict.values():
            v["correct"] = 0
            v["total"] = 0

    for stats_dict in (
        domain_times_last,
        difficulty_times_last,
        domain_times_alltime,
        difficulty_times_alltime,
    ):
        for v in stats_dict.values():
            v.clear()

    all_stats_last["correct"] = all_stats_last["total"] = 0
    all_stats_alltime["correct"] = all_stats_alltime["total"] = 0
    all_times_last.clear()
    all_times_alltime.clear()
    update_table()
    print("cleared user data")

def reset_questions():
    global qCompleted, qUncompleted, filteredQuestions
    qCompleted.clear()
    # Rebuild filteredQuestions and qUncompleted from rawQuestions
    make_set()
    print('Questions reset - qUncompleted: ', qUncompleted)

def on_close():
    stats = {
        "last": {
            "domain times": domain_times_last,
            "difficulty times": difficulty_times_last,
            "overall times": all_times_last,
            "domain": domain_stats_last,
            "difficulty": difficulty_stats_last,
            "overall": all_stats_last
        },
        "alltime": {
            "domain times": domain_times_alltime,
            "difficulty times": difficulty_times_alltime,
            "overall times": all_times_alltime,
            "domain": domain_stats_alltime,
            "difficulty": difficulty_stats_alltime,
            "overall": all_stats_alltime
        },
        "qCompleted": qCompleted,
    }
    print('saving user data to user_data.json')
    with open("user_data.json", "w") as f:
        json.dump(stats, f, indent=2)

    w.destroy()

def update_timer():
    global timer_job, time, tick
    if tick % 10 == 0:
        try:
            infoLabel.config(
                text=f"Last Question: {'Correct' if wasCorrect else f'Incorrect ({correct})'} | Questions remaining: {len(filteredQuestions) + 1} | Time elapsed: {time}")
        except NameError:
            infoLabel.config(text=f"Questions remaining: {len(filteredQuestions) + 1} | Time elapsed: {time}")
        time += 1
    tick += 1
    timer_job = w2.after(100, update_timer)

def checkbox_dropdown(parent, label, options_dict):
    mb = Menubutton(parent, text=label, relief="raised")
    menu = Menu(mb, tearoff=0)
    mb.config(menu=menu)

    for text, var in options_dict.items():
        menu.add_checkbutton(label=text, variable=var)

    mb.pack(fill="both", expand=True)
    return mb

def make_set():
    global filteredQuestions, qUncompleted
    selected_domains = {name for name, var in domain_flags.items() if var.get()}
    selected_difficulties = {name for name, var in difficulty_flags.items() if var.get()}

    filteredQuestions = [
        q for q in rawQuestions
        if (not selected_domains or q["domain"] in selected_domains)
           and (not selected_difficulties or q["difficulty"] in selected_difficulties)]

    qUncompleted = [q["id"] for q in filteredQuestions if q["id"] not in qCompleted]
    print('qUncompleted: ', qUncompleted)

def cell(text, r, c): #makes editable cells for the table
    lbl = Label(bottomFrame, text=text, borderwidth=1, relief="solid")
    lbl.grid(row=r, column=c, sticky="nsew")
    cells[(r, c)] = lbl

def rand_question():
    global correct, filteredQuestions, time, currentDiff, currentDom
    time = 0
    r = randint(0,len(qUncompleted)-1)
    qid = qUncompleted.pop(randint(0, len(qUncompleted) - 1))
    qCompleted.append(qid)
    print('not seen questions indices: ', *qUncompleted)
    print('seen questions indices: ', *qCompleted)
    q = next(q for q in filteredQuestions if q["id"] == qid)
    filteredQuestions.remove(q)
    currentDiff = q["difficulty"]
    currentDom = q["domain"]
    correct = q['correct']
    print('Correct: ' + correct)
    #update ui
    dataLabel.config(text=f"ID: {q['id']} | Test: {q['test']} | Domain: {q['domain']} | Skill: {q['skill']} | Difficulty: {q['difficulty']}")
    passage.config(text=q['passage'],width=width)
    question.config(text=q['question'],width=width)
    ansA.config(text=q['choices'][0]['text'])
    ansB.config(text=q['choices'][1]['text'])
    ansC.config(text=q['choices'][2]['text'])
    ansD.config(text=q['choices'][3]['text'])
    try:
        infoLabel.config(text=f"Last Question: {'Correct' if wasCorrect else f'Incorrect ({correct})'} | Questions remaining: {len(filteredQuestions)+1} | Time elapsed: {time}")
    except NameError:
        infoLabel.config(text=f"Questions remaining: {len(filteredQuestions)+1} | Time elapsed: {time}")
    return correct, r

def record_answer(domain, difficulty, was_correct):
    # domain accuracy
    domain_stats_last[domain]["total"] += 1
    domain_stats_alltime[domain]["total"] += 1
    domain_times_last[domain].append(time)
    domain_times_alltime[domain].append(time)
    if was_correct:
        domain_stats_last[domain]["correct"] += 1
        domain_stats_alltime[domain]["correct"] += 1

    # difficulty accuracy
    difficulty_stats_last[difficulty]["total"] += 1
    difficulty_stats_alltime[difficulty]["total"] += 1
    difficulty_times_last[difficulty].append(time)
    difficulty_times_alltime[difficulty].append(time)
    if was_correct:
        difficulty_stats_last[difficulty]["correct"] += 1
        difficulty_stats_alltime[difficulty]["correct"] += 1

    # all row
    all_stats_last["total"] += 1
    all_stats_alltime["total"] += 1
    all_times_last.append(time)
    all_times_alltime.append(time)
    if was_correct:
        all_stats_last["correct"] += 1
        all_stats_alltime["correct"] += 1
    update_table()

def update_table():
    x = 1
    for domain in domain_flags: # loops thru each domain
        cell(f'{round(domain_stats_alltime[domain]['correct']/domain_stats_alltime[domain]['total']*100)}%' if domain_stats_alltime[domain]["total"] else '—',x,1) # updates table
        cell(f'{round(domain_stats_last[domain]['correct'] / domain_stats_last[domain]['total'] * 100)}%' if domain_stats_last[domain]["total"] else '—', x, 2)
        cell(avg_times(domain_times_alltime[domain]), x, 3)
        cell(avg_times(domain_times_last[domain]), x, 4)
        x += 1
    x = 5
    for difficulty in difficulty_flags:
        cell(f"{round(difficulty_stats_alltime[difficulty]['correct'] / difficulty_stats_alltime[difficulty]['total'] * 100)}%" if difficulty_stats_alltime[difficulty]["total"] else '—',x, 1)
        cell(f"{round(difficulty_stats_last[difficulty]['correct'] / difficulty_stats_last[difficulty]['total'] * 100)}%" if difficulty_stats_last[difficulty]["total"] else '—',x, 2)
        cell(avg_times(difficulty_times_alltime[difficulty]), x, 3)
        cell(avg_times(difficulty_times_last[difficulty]), x, 4)
        x += 1
    cell(f'{round(all_stats_alltime['correct'] / all_stats_alltime['total'] * 100)}%' if all_stats_alltime['total'] else '—',8, 1)
    cell(f'{round(all_stats_last['correct'] / all_stats_last['total'] * 100)}%' if all_stats_last['total'] else '—', 8, 2)
    cell(avg_times(all_times_alltime), 8, 3)
    cell(avg_times(all_times_last), 8, 4)

def submit():
    global numCorrect, numIncorrect, correct, wasCorrect
    if len(filteredQuestions) <= 1:
        submitButton.config(text="Complete test")
    wasCorrect = choice.get() == correct
    if wasCorrect:
        numCorrect += 1
        #print('diiing')
    else:
        numIncorrect += 1
        #print('wronnnng')
    record_answer(currentDom, currentDiff, wasCorrect)
    #qTimes_last.append(time) delete later
    #qTimes_alltime.append(time)
    try:
        correct, r = rand_question()
    except ValueError:
        dataLabel.destroy()
        passage.destroy()
        question.destroy()
        ansA.destroy()
        ansB.destroy()
        ansC.destroy()
        ansD.destroy()
        infoLabel.destroy()
        submitButton.destroy()
        w2.minsize(500, 350)
        print('out of questions!')

def skip():
    global correct
    if len(filteredQuestions) <= 1:
        submitButton.config(text="Complete test")
    try:
        correct, r = rand_question()
    except ValueError:
        dataLabel.destroy()
        passage.destroy()
        question.destroy()
        ansA.destroy()
        ansB.destroy()
        ansC.destroy()
        ansD.destroy()
        infoLabel.destroy()
        submitButton.destroy()
        w2.minsize(500, 350)
        print('out of questions!')

def testing_window():
    global passage, question, ansA, ansB, ansC, ansD, choice, correct, dataLabel, infoLabel, submitButton, w2, all_times_last
    #window setup
    w2 = Toplevel()
    w2.title('Testing Window')
    w2.minsize(850, 250)
    myFont = font.Font(family='Helvetica', size=15)
    #reset last dictionaries
    for d in domain_stats_last.values(): d["correct"] = d["total"] = 0
    for d in difficulty_stats_last.values(): d["correct"] = d["total"] = 0
    for d in domain_times_last.values(): d.clear()
    for d in difficulty_times_last.values(): d.clear()
    all_stats_last["correct"] = all_stats_last["total"] = 0
    all_times_last.clear()

    #multiple choice choice
    choice = StringVar(value='', master=w2)
    #info row
    dataLabel = Label(w2, text="data row", font=myFont)
    dataLabel.pack(fill="x", padx=5, pady=5)
    #packing
    passage = Message(w2, text="Passage default", font=myFont)
    passage.pack(anchor='w', expand=True, fill=BOTH)

    question = Message(w2, text="Question default", font=myFont)
    question.pack(anchor='w', expand=True, fill=BOTH)

    ansA = Radiobutton(w2, variable=choice, value='A', wraplength=width, anchor='w', justify="left", font=myFont); ansA.pack(anchor='w')
    ansB = Radiobutton(w2, variable=choice, value='B', wraplength=width, anchor='w', justify="left", font=myFont); ansB.pack(anchor='w')
    ansC = Radiobutton(w2, variable=choice, value='C', wraplength=width, anchor='w', justify="left", font=myFont); ansC.pack(anchor='w')
    ansD = Radiobutton(w2, variable=choice, value='D', wraplength=width, anchor='w', justify="left", font=myFont); ansD.pack(anchor='w')

    infoLabel = Label(w2, text="info row", font=myFont); infoLabel.pack(side="left")

    submitButton = Button(w2, text="Submit", command=submit, font=myFont); submitButton.pack(side="right")
    skipButton = Button(w2, text="Skip", command=skip, font=myFont); skipButton.pack(side="right")

    update_timer()

    correct, r = rand_question()

    w2.mainloop()

#frames
topFrame = Frame(w)
bottomFrame = Frame(w)
optionsFrame = Frame(topFrame)

#configured widgets
checkbox_dropdown(optionsFrame, "Domain", domain_flags)

checkbox_dropdown(optionsFrame, "Difficulty", difficulty_flags)

#makes stats spreadsheet
cell("Stats", 0, 0)
cell("All time🎯", 0, 1)
cell("Previous🎯", 0, 2)
cell('All time⏳', 0, 3)
cell('Previous⏳', 0, 4)

for x in domain_flags:
    if x == "Standard English Conventions":
        cell("Conventions", list(domain_flags.keys()).index(x)+1, 0)
    else:
        cell(x, list(domain_flags.keys()).index(x)+1, 0)
for x in difficulty_flags:
    cell(x, list(difficulty_flags.keys()).index(x)+5, 0)
cell("All",8,0)

#pack
topFrame.pack(fill=BOTH, expand=True, side=TOP)
for x in range(6):
    topFrame.grid_columnconfigure(x,weight=1)
topFrame.grid_rowconfigure(0, weight=1)
topFrame.grid_rowconfigure(1, weight=2)
Button(topFrame, text="Start",command=testing_window).grid(row=0, column=0, columnspan=3, sticky="nsew")
optionsFrame.grid(row=0, column=3, columnspan=3, sticky="nsew")
Button(topFrame, text='Reset data', command=clear_usrData).grid(row=1, column=0, columnspan=2, sticky="nsew")
Button(topFrame, text='Reset questions', command=reset_questions).grid(row=1, column=2, columnspan=2, sticky="nsew")
Button(topFrame, text="Create set", command=make_set).grid(row=1, column=4, columnspan=2, sticky="nsew")
make_set()

bottomFrame.pack(fill=BOTH, expand=True)
bottomFrame.grid_rowconfigure(9, weight=1)
bottomFrame.grid_columnconfigure(4, weight=1)
for x in range(9): #rows
    bottomFrame.grid_rowconfigure(x, weight=1)
    if x != 8:
        for y in range(4): #cols
            bottomFrame.grid_columnconfigure(y, weight=1)
            cell('NA',x+1,y+1)
update_table()

w.protocol("WM_DELETE_WINDOW", on_close)
w.mainloop()