from tkinter import *
from tkinter import font
from tkinter import ttk
from random import randint
import json
import os
import re
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.patches as mpatches

with open('jsons/extendedDataTest.json', 'r') as file:
    rawQuestions = json.load(file)

w = Tk()
w.title('Prepster')
w.minsize(410, 285)

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
width = 900

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

def cell(text, r, c):
    lbl = Label(bottomFrame, text=text, borderwidth=1, relief="solid")
    lbl.grid(row=r, column=c, sticky="nsew")
    cells[(r, c)] = lbl

def create_table_widget(parent, table_data, myFont):
    """
    Create a table widget from the table data structure.
    """
    table_frame = Frame(parent, relief="solid", borderwidth=1)
    
    if table_data.get("title"):
        title_label = Label(table_frame, text=table_data["title"], font=myFont, anchor="w")
        title_label.pack(fill="x", padx=5, pady=(5, 0))
    
    table_grid = Frame(table_frame)
    table_grid.pack(fill="both", expand=True, padx=5, pady=5)
    
    for row_idx, row_data in enumerate(table_data["rows"]):
        row_type = row_data["type"]
        cells = row_data["cells"]
        
        for col_idx, cell_text in enumerate(cells):
            if row_type == "header":
                cell_label = Label(table_grid, text=cell_text, relief="solid", 
                                 borderwidth=1, font=(myFont.actual()['family'], myFont.actual()['size'], 'bold'),
                                 bg="#919191", anchor="w", padx=5, pady=3)
            else:
                cell_label = Label(table_grid, text=cell_text, relief="solid", 
                                 borderwidth=1, font=myFont, anchor="w", padx=5, pady=3)
            
            cell_label.grid(row=row_idx, column=col_idx, sticky="nsew")
            table_grid.grid_columnconfigure(col_idx, weight=1)
    
    return table_frame

def create_chart_widget(parent, chart_data):
    """
    Create a matplotlib chart widget from chart data.
    Supports both 'bar' and 'line' chart types.
    """
    chart_frame = Frame(parent)
    
    # Create matplotlib figure
    fig = Figure(figsize=(6, 3.5), dpi=80)
    ax = fig.add_subplot(111)
    
    chart_type = chart_data.get("type", "line")
    
    if chart_type == "bar":
        create_bar_chart(ax, chart_data)
    elif chart_type == "line":
        create_line_chart(ax, chart_data)
    
    # Add title
    if chart_data.get("title"):
        ax.set_title(chart_data["title"], fontsize=12, pad=10, wrap=True)
    
    # Embed the figure in Tkinter
    canvas = FigureCanvasTkAgg(fig, master=chart_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=BOTH, expand=True)
    
    return chart_frame

def create_bar_chart(ax, chart_data):
    """
    Create a grouped bar chart.
    """
    categories = chart_data.get("categories", [])
    series_list = chart_data.get("series", [])
    
    x = range(len(categories))
    width = 0.8 / len(series_list) if series_list else 0.8
    
    # Plot each series
    for i, series in enumerate(series_list):
        offset = (i - len(series_list) / 2) * width + width / 2
        positions = [pos + offset for pos in x]
        ax.bar(positions, series["values"], width, 
               label=series.get("label", f"Series {i+1}"),
               color=series.get("color", "#808080"))
    
    # Configure axes
    ax.set_xticks(x)
    ax.set_xticklabels(categories, rotation=0, ha='center')
    ax.set_ylabel(chart_data.get("y_label", ""))
    ax.set_xlabel(chart_data.get("x_label", ""))
    
    # Add grid
    if chart_data.get("grid", True):
        ax.grid(axis='y', alpha=0.3)
    
    # Add legend if multiple series
    if len(series_list) > 1:
        ax.legend(loc='best')
    
    # Set y-axis limits if provided
    if "y_axis" in chart_data:
        y_axis = chart_data["y_axis"]
        if "min" in y_axis and "max" in y_axis:
            ax.set_ylim(y_axis["min"], y_axis["max"])

def create_line_chart(ax, chart_data):
    """
    Create a line chart with multiple series.
    Supports different line styles and markers.
    """
    x_values = chart_data.get("x_axis", {}).get("values", [])
    series_list = chart_data.get("series", [])
    
    # Marker style mapping
    marker_map = {
        "circle": "o",
        "square": "s",
        "triangle": "^",
        "star": "*",
        "diamond": "D",
        "none": ""
    }
    
    # Line style mapping
    style_map = {
        "solid": "-",
        "dashed": "--",
        "dotted": ":",
        "dashdot": "-."
    }
    
    # Plot each series
    for series in series_list:
        data = series.get("data", [])
        label = series.get("label", "")
        color = series.get("color", "#000000")
        marker = marker_map.get(series.get("marker", "circle"), "o")
        line_style = style_map.get(series.get("style", "solid"), "-")
        
        # Plot with markers and lines
        ax.plot(x_values, data, 
                label=label,
                color=color,
                linestyle=line_style,
                marker=marker,
                markersize=8,
                markerfacecolor='white' if marker in ['o', 's'] else color,
                markeredgecolor=color,
                markeredgewidth=2,
                linewidth=2)
    
    # Configure axes
    ax.set_xlabel(chart_data.get("x_axis", {}).get("label", ""))
    ax.set_ylabel(chart_data.get("y_axis", {}).get("label", ""))
    
    # Set y-axis limits if provided
    if "y_axis" in chart_data:
        y_axis = chart_data["y_axis"]
        if "min" in y_axis and "max" in y_axis:
            ax.set_ylim(y_axis["min"], y_axis["max"])
        if "tick_interval" in y_axis:
            import numpy as np
            ticks = np.arange(y_axis.get("min", 0), 
                            y_axis.get("max", 100) + 1, 
                            y_axis["tick_interval"])
            ax.set_yticks(ticks)
    
    # Add grid
    if chart_data.get("grid", True):
        ax.grid(True, alpha=0.3)
    
    # Add legend
    if len(series_list) > 1:
        ax.legend(loc='best', frameon=True)
    
    # Rotate x-axis labels if needed
    if len(x_values) > 8:
        ax.tick_params(axis='x', rotation=45)

def set_text_with_underlines(text_widget, content, text_font):
    """
    Set text in a Text widget, underlining any ALL CAPS words/phrases.
    ALL CAPS is defined as 2+ consecutive uppercase letters.
    """
    text_widget.config(state='normal')
    text_widget.delete('1.0', END)
    
    # Configure tags
    text_widget.tag_configure('underline', underline=True)
    
    # Split and process text
    # Pattern: Find sequences of 2+ uppercase letters (with optional spaces between words)
    pattern = r'\b[A-Z]{2,}(?:\s+[A-Z]{2,})*\b'
    
    last_end = 0
    for match in re.finditer(pattern, content):
        # Insert text before the match
        if match.start() > last_end:
            text_widget.insert(END, content[last_end:match.start()])
        
        # Insert the ALL CAPS text with underline, but display it in normal case
        caps_text = match.group()
        # Convert to title case for display while keeping underline
        display_text = caps_text.title()
        text_widget.insert(END, display_text, 'underline')
        
        last_end = match.end()
    
    # Insert remaining text
    if last_end < len(content):
        text_widget.insert(END, content[last_end:])
    
    # Auto-adjust height based on line count
    line_count = int(text_widget.index('end-1c').split('.')[0])
    line_count = max(1, min(line_count, 25))  # Keep between 1 and 25 lines
    text_widget.config(height=line_count)
    
    text_widget.config(state='disabled')

def rand_question():
    global correct, filteredQuestions, time, currentDiff, currentDom, tableFrame, chartFrame
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
    
    # Handle table display
    if 'tableFrame' in globals() and tableFrame is not None:
        tableFrame.destroy()
        tableFrame = None
    
    # Handle chart display
    if 'chartFrame' in globals() and chartFrame is not None:
        chartFrame.destroy()
        chartFrame = None
    
    # Display table if present
    if "table" in q and q["table"]:
        myFont = font.Font(family='Helvetica', size=15)
        tableFrame = create_table_widget(contentFrame, q["table"], myFont)
        tableFrame.pack(fill="x", padx=5, pady=(5, 0), before=passage)
    
    # Display chart if present
    if "chart" in q and q["chart"]:
        chartFrame = create_chart_widget(contentFrame, q["chart"])
        chartFrame.pack(fill="both", expand=True, padx=5, pady=(5, 0), before=passage)
    
    #update ui
    dataLabel.config(text=f"ID: {q['id']}   |   Test: {q['test']}   |   Domain: {q['domain']}   |   Skill: {q['skill']}   |   Difficulty: {q['difficulty']}",
                     font=font.Font(family='Helvetica', size=9))
    
    # Set passage and question.
    # Use the underline-aware setter for the passage Text widget.
    myFont = font.Font(family='Helvetica', size=15)
    set_text_with_underlines(passage, q['passage'], myFont)
    
    # Question is a Label, so just set the text directly.
    question.config(text=q['question'])
    
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
    domain_stats_last[domain]["total"] += 1
    domain_stats_alltime[domain]["total"] += 1
    domain_times_last[domain].append(time)
    domain_times_alltime[domain].append(time)
    if was_correct:
        domain_stats_last[domain]["correct"] += 1
        domain_stats_alltime[domain]["correct"] += 1

    difficulty_stats_last[difficulty]["total"] += 1
    difficulty_stats_alltime[difficulty]["total"] += 1
    difficulty_times_last[difficulty].append(time)
    difficulty_times_alltime[difficulty].append(time)
    if was_correct:
        difficulty_stats_last[difficulty]["correct"] += 1
        difficulty_stats_alltime[difficulty]["correct"] += 1

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
    for domain in domain_flags:
        cell(f'{round(domain_stats_alltime[domain]['correct']/domain_stats_alltime[domain]['total']*100)}%' if domain_stats_alltime[domain]["total"] else '—',x,1)
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
    else:
        numIncorrect += 1
    record_answer(currentDom, currentDiff, wasCorrect)
    try:
        correct, r = rand_question()
    except ValueError:
        dataLabel.destroy()
        if 'tableFrame' in globals() and tableFrame is not None:
            tableFrame.destroy()
        if 'chartFrame' in globals() and chartFrame is not None:
            chartFrame.destroy()
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
        if 'tableFrame' in globals() and tableFrame is not None:
            tableFrame.destroy()
        if 'chartFrame' in globals() and chartFrame is not None:
            chartFrame.destroy()
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
    global passage, question, ansA, ansB, ansC, ansD, choice, correct, dataLabel, infoLabel, submitButton, w2, all_times_last, contentFrame, tableFrame, chartFrame
    
    w2 = Toplevel()
    w2.title('Testing Window')
    w2.minsize(850, 250)
    myFont = font.Font(family='Helvetica', size=15)
    
    tableFrame = None
    chartFrame = None
    
    #reset last dictionaries
    for d in domain_stats_last.values(): d["correct"] = d["total"] = 0
    for d in difficulty_stats_last.values(): d["correct"] = d["total"] = 0
    for d in domain_times_last.values(): d.clear()
    for d in difficulty_times_last.values(): d.clear()
    all_stats_last["correct"] = all_stats_last["total"] = 0
    all_times_last.clear()

    choice = StringVar(value='', master=w2)
    
    dataLabel = Label(w2, text="data row")
    dataLabel.pack(fill="x", padx=2, pady=2)
    
    contentFrame = Frame(w2)
    contentFrame.pack(anchor='w', expand=True, fill=BOTH)
    
    # Use Text widget instead of Message to support underlines. Height will auto-adjust
    # based on content via set_text_with_underlines(). Match the default window background
    # with a border outline and white text.
    passage = Text(contentFrame, wrap=WORD, font=myFont,
                   bd=1, relief='solid', bg=w2.cget('bg'), fg='white', highlightthickness=0)
    passage.pack(anchor='w', expand=True, fill=BOTH, padx=5)

    # Question: use a fixed-height frame so expansion goes to passage.
    questionFrame = Frame(contentFrame)
    questionFrame.pack(anchor='w', fill='x', padx=5, pady=5)
    question = Label(questionFrame, wraplength=width, font=myFont, justify="left", anchor="nw")
    question.pack(anchor='w', fill=BOTH)

    # Answers: use a fixed-height frame so expansion goes to passage.
    answerFrame = Frame(w2)
    answerFrame.pack(anchor='w', fill='x')
    ansA = Radiobutton(answerFrame, variable=choice, value='A', wraplength=width, anchor='w', justify="left", font=myFont); ansA.pack(anchor='w')
    ansB = Radiobutton(answerFrame, variable=choice, value='B', wraplength=width, anchor='w', justify="left", font=myFont); ansB.pack(anchor='w')
    ansC = Radiobutton(answerFrame, variable=choice, value='C', wraplength=width, anchor='w', justify="left", font=myFont); ansC.pack(anchor='w')
    ansD = Radiobutton(answerFrame, variable=choice, value='D', wraplength=width, anchor='w', justify="left", font=myFont); ansD.pack(anchor='w')

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
for x in range(9):
    bottomFrame.grid_rowconfigure(x, weight=1)
    if x != 8:
        for y in range(4):
            bottomFrame.grid_columnconfigure(y, weight=1)
            cell('NA',x+1,y+1)
update_table()

w.protocol("WM_DELETE_WINDOW", on_close)
w.mainloop()