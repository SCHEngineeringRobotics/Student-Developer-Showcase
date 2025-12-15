from multiprocessing.connection import answer_challenge
from tkinter import *
from random import randint
import json

with open('parsed_sat_questions.json', 'r') as file:
    rawQuestions = json.load(file)
print(rawQuestions[0]['id'])
#print(json.dumps(data, indent=4))

w = Tk()
w.title('Prepster')
w.minsize(300, 315)

#vars
Information_and_Ideas = BooleanVar()
Craft_and_Structure = BooleanVar()
Expression_of_Ideas = BooleanVar()
Standard_English_Conventions = BooleanVar()
easy = BooleanVar()
med = BooleanVar()
hard = BooleanVar()
timed = BooleanVar()

domain_flags = {
    "Information and Ideas": Information_and_Ideas,
    "Craft and Structure": Craft_and_Structure,
    "Expression of Ideas": Expression_of_Ideas,
    "Standard English Conventions": Standard_English_Conventions
}
difficulty_flags = {
    "Easy": easy,
    "Medium": med,
    "Hard": hard
}

correct = {}
incorrect = {}

cells = {}
#funcs
def show_selected():
    selected_domains = {name for name, var in domain_flags.items() if var.get()}
    selected_difficulties = {name for name, var in difficulty_flags.items() if var.get()}
    selected_timed = timed.get()
    print("domains: ", selected_domains)
    print('difficulties: ', selected_difficulties)
    print("timed: "+ str(selected_timed))

def cell(text, r, c): #makes editable cells for the table
    lbl = Label(bottomFrame, text=text, borderwidth=1, relief="solid")
    lbl.grid(row=r, column=c, sticky="nsew")
    cells[(r, c)] = lbl

def randdata(): #puts random data in all the cells (testing)
    for x in range(7):
        for y in range(3):
            cell(f'{randint(0,100)}%', x + 1, y + 1)

def resize(event):
    passage.config(width=event.width)
    question.config(width=event.width)

def rand_question():
    global correct
    r = randint(0,len(rawQuestions))
    passage.config(text=rawQuestions[r]['passage'])
    question.config(text=rawQuestions[r]['question'])
    ansA.config(text=rawQuestions[r]['choices'][0]['text'])
    ansB.config(text=rawQuestions[r]['choices'][1]['text'])
    ansC.config(text=rawQuestions[r]['choices'][2]['text'])
    ansD.config(text=rawQuestions[r]['choices'][3]['text'])
    correct = rawQuestions[r]['correct']
    print(correct)

def button():
    testing_window()

def testing_window():
    global passage, question, ansA, ansB, ansC, ansD
    w2 = Tk()
    w2.title('Testing Window')
    w2.minsize(715, 300)
    w2.bind("<Configure>", resize)

    choice = IntVar()

    passage = Message(w2, text="Passage default")
    passage.pack(anchor='w', expand=True, fill=BOTH)

    question = Message(w2, text="Question default")
    question.pack(anchor='w', expand=True, fill=BOTH)

    ansA = Radiobutton(w2, variable=choice, value=0, wraplength=700, anchor='w', justify="left")
    ansA.pack(anchor='w')

    ansB = Radiobutton(w2, variable=choice, value=1, wraplength=700, anchor='w', justify="left")
    ansB.pack(anchor='w')

    ansC = Radiobutton(w2, variable=choice, value=2, wraplength=700, anchor='w', justify="left")
    ansC.pack(anchor='w')

    ansD = Radiobutton(w2, variable=choice, value=3, wraplength=700, anchor='w', justify="left")
    ansD.pack(anchor='w')

    Button(w2, text="Submit", command=rand_question).pack()

    rand_question()

    w2.mainloop()

#frames
topFrame = Frame(w)
bottomFrame = Frame(w)
optionsFrame = Frame(topFrame)
for i in range(4):   # columns
    bottomFrame.grid_columnconfigure(i, weight=1)
for i in range(8):   # rows
    bottomFrame.grid_rowconfigure(i, weight=1)

#widgets
startButton = Button(topFrame, text="Start",command=button)

Label(optionsFrame, text="Domain").pack()
Checkbutton(optionsFrame, text="Information and Ideas", variable=Information_and_Ideas).pack(anchor='w')
Checkbutton(optionsFrame, text="Craft and Structure", variable=Craft_and_Structure).pack(anchor='w')
Checkbutton(optionsFrame, text="Expression of Ideas", variable=Expression_of_Ideas).pack(anchor='w')
Checkbutton(optionsFrame, text="Standard English Conventions", variable=Standard_English_Conventions).pack(anchor='w')
Label(optionsFrame, text="Difficulty").pack()
Checkbutton(optionsFrame, text="Easy", variable=easy).pack(anchor='w')
Checkbutton(optionsFrame, text="Medium", variable=med).pack(anchor='w')
Checkbutton(optionsFrame, text="Hard",variable=hard).pack(anchor='w')
Label(optionsFrame, text="Other").pack()
Checkbutton(optionsFrame, text="Timed", variable=timed).pack(anchor='w')



#makes stats spreadsheet
cell("Stats", 0, 0)
cell("Avg", 0, 1)
cell("1st", 0, 2)
cell("Last", 0, 3)
for x in domain_flags:
    cell(x, list(domain_flags.keys()).index(x)+1, 0)
for x in difficulty_flags:
    cell(x, list(difficulty_flags.keys()).index(x)+5, 0)
for x in range(7):
    for y in range(3):
        cell('00%',x+1,y+1)

#pack
topFrame.pack(fill=BOTH, expand=True, side=TOP)
topFrame.grid_columnconfigure(0,weight=1)
topFrame.grid_rowconfigure(0,weight=1)
bottomFrame.pack(fill=BOTH, expand=True, side=TOP)
startButton.grid(row=0, column=0, sticky="nsew")
optionsFrame.grid(row=0, column=1, sticky="nsew")

Button(optionsFrame, text="button", command=show_selected).pack()

w.mainloop()