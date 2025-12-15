import pdfplumber
import re
import json

# Match question IDs
ID_PATTERN = re.compile(r"Question ID\s+([0-9a-f]+)", re.I)

# Match correct answer
CORRECT_PATTERN = re.compile(r"Correct Answer:\s*([A-D])", re.I)

# Capture the last sentence before the answer choices (A., B., C., D.)
QUESTION_SENTENCE = re.compile(
    r"\n([^\n]+?)\s*(?=\s*[A-D]\.)",
    re.S)

# Robust choice detection (fix for A. missing problem)
CHOICE_START = re.compile(r"(?:^|\s)([A-D])\.\s", re.M)

def clean(text):
    if not text:
        return ""
    return " ".join(text.split())


def extract_pages(pdf_path):
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, p in enumerate(pdf.pages, start=1):
            txt = p.extract_text() or ""
            pages.append({"page": i, "text": txt})
    return pages


def split_into_question_blocks(full_text):
    """Splits the entire PDF text into blocks starting with Question ID."""
    parts = re.split(r"(Question ID\s+[0-9a-f]+)", full_text, flags=re.I)
    blocks = []

    # Pair header with following text
    for i in range(1, len(parts), 2):
        blocks.append(parts[i] + "\n" + parts[i + 1])

    return blocks


def parse_choices(block):
    """Extracts choices A, B, C, D using robust position-based slicing."""
    choices = []
    matches = list(CHOICE_START.finditer(block))

    if not matches:
        return []

    for i, m in enumerate(matches):
        label = m.group(1)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(block)
        text = block[start:end].strip()

        # Strip trailing junk like ID:, Answer, Rationale, etc.
        text = re.split(r"(Correct Answer|Rationale|Question ID|ID:|Answer\b)", text, flags=re.I)[0]

        choices.append({
            "label": label,
            "text": clean(text)
        })

    return choices

def extract_metadata(block):
    lines = [ln.strip() for ln in block.splitlines() if ln.strip()]

    # 1. Find the labels line
    label_idx = None
    for i, ln in enumerate(lines):
        if all(x in ln.lower() for x in ["assessment", "test", "domain", "skill", "difficulty"]):
            label_idx = i
            break

    if label_idx is None:
        return {"test": None, "domain": None, "skill": None, "difficulty": None}

    # 2. Collect value lines until ID:
    value_lines = []
    for ln in lines[label_idx + 1:]:
        if ln.startswith("ID:"):
            break
        value_lines.append(ln)

    # 3. Merge lines
    merged = " ".join(value_lines)

    # 4. Split by large gaps (fallback removes this anyway)
    cols = re.split(r"\s{2,}", merged)
    if len(cols) < 5:
        cols = merged.split()

    # Known ordering:
    test = None
    domain = None
    skill = None

    # Detect "Reading and Writing"
    if "Reading" in cols and "Writing" in cols:
        ri = cols.index("Reading")
        test = "Reading and Writing"
        del cols[ri:ri+3]

    # Known domains list
    known_domains = [
        "Information and Ideas",
        "Craft and Structure",
        "Expression of Ideas",
        "Standard English Conventions"
    ]
    for d in known_domains:
        parts = d.split()
        if all(w in cols for w in parts):
            domain = d
            for w in parts:
                cols.remove(w)
            break

    # Skill = remaining words before difficulty bars
    remaining = []
    for c in cols:
        if set(c) <= set("●○□■▬▮"):
            break
        remaining.append(c)
    skill = " ".join(remaining) if remaining else None

    #Fix: strip leading “SAT ”
    if skill and skill.startswith("SAT "):
        skill = skill[4:]

    # Difficulty
    m = re.search(r"Question Difficulty:\s*([A-Za-z]+)", block)
    difficulty = m.group(1) if m else None

    return {
        "test": test,
        "domain": domain,
        "skill": skill,
        "difficulty": difficulty
    }


def parse_block(block):
    """Extracts id, passage, question, choices, correct answer, rationale."""
    q = {}

    # Question ID
    id_match = ID_PATTERN.search(block)
    if not id_match:
        return None  # Skip blocks without ID
    q["id"] = id_match.group(1)

    meta = extract_metadata(block)
    q["test"] = meta.get("test")
    q["domain"] = meta.get("domain")
    q["skill"] = meta.get("skill")
    q["difficulty"] = meta.get("difficulty")

    # ----- Extract question sentence -----
    q_sentence = QUESTION_SENTENCE.search(block)
    if q_sentence:
        q["question"] = clean(q_sentence.group(1))
    else:
        q["question"] = ""

    # ----- Extract passage text -----
    # Start passage immediately after the "ID: xxxxxx" line (blue box)
    id_line_match = re.search(r"ID:\s*([0-9a-f]{6,})\s*\n", block, re.I)
    passage_start = id_line_match.end() if id_line_match else 0

    if q_sentence:
        passage_raw = block[passage_start : q_sentence.start()]
    else:
        passage_raw = block[passage_start:]

    q["passage"] = clean(passage_raw)

    # ----- Extract choices -----
    q["choices"] = parse_choices(block)

    # ----- Extract correct answer -----
    ans_match = CORRECT_PATTERN.search(block)
    q["correct"] = ans_match.group(1) if ans_match else None

    # ----- Extract rationale -----
    if "Rationale" in block:
        rationale = block.split("Rationale", 1)[1]
        rationale = rationale.split("Question Difficulty")[0]
        q["rationale"] = clean(rationale)
    else:
        q["rationale"] = ""

    return q


def parse_pdf(path):
    """Main driver. Reads PDF -> splits blocks -> parses each question."""
    pages = extract_pages(path)
    full_text = "\n".join(p["text"] for p in pages)
    blocks = split_into_question_blocks(full_text)

    questions = []
    for b in blocks:
        q = parse_block(b)
        if q:
            questions.append(q)

    return questions

if __name__ == "__main__":
    input_pdf = "SAT Suite Question Bank - Results.pdf"  # <-- Make sure your renamed PDF is here
    output_json = "parsed_sat_questions.json"

    results = parse_pdf(input_pdf)

    with open(output_json, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Extracted {len(results)} questions → {output_json}")