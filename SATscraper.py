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

# Robust choice detection
CHOICE_START = re.compile(r"(?:^|\s)([A-D])\.\s", re.M)


def clean(text):
    if not text:
        return ""
    return " ".join(text.split())


def is_metadata_table(table):
    """Check if a table is the metadata header (not actual content)."""
    if not table or len(table) < 1:
        return True

    # Convert all cells to strings
    flat_content = " ".join(
        str(cell).lower()
        for row in table
        for cell in row
        if cell
    )

    # Metadata tables contain these keywords
    metadata_keywords = ["assessment", "domain", "skill", "difficulty", "test"]
    keyword_count = sum(1 for kw in metadata_keywords if kw in flat_content)

    # If 3+ metadata keywords, it's a metadata table
    if keyword_count >= 3:
        return True

    # Check if table contains the Question ID pattern
    if re.search(r"id[:\s]*[0-9a-f]{6,}", flat_content, re.I):
        return True

    return False


def extract_pages(pdf_path):
    """Extract text and tables from each page using optimized settings."""
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, p in enumerate(pdf.pages, start=1):
            txt = p.extract_text() or ""

            # Extract tables with settings that prioritize visible lines
            table_settings = {
                "vertical_strategy": "lines",
                "horizontal_strategy": "lines",
                "snap_tolerance": 10,  # Increased to merge nearby lines
                "join_tolerance": 10,  # Increased to merge nearby lines
                "edge_min_length": 30,  # Reduced to catch shorter lines
                "intersection_tolerance": 15,  # Added: merge line intersections
            }

            try:
                tables = p.extract_tables(table_settings=table_settings)
            except:
                # Fallback to default if custom settings fail
                tables = p.extract_tables()

            # Filter out metadata tables
            content_tables = [t for t in tables if t and not is_metadata_table(t)]

            pages.append({
                "page": i,
                "text": txt,
                "tables": content_tables
            })
    return pages


def merge_split_cells(table):
    """
    Merge cells that appear to be incorrectly split.
    Example: ['Pyram', 'id'] -> ['Pyramid']
    """
    if not table or len(table) < 1:
        return table

    merged_table = []

    for row in table:
        merged_row = []
        i = 0

        while i < len(row):
            current = str(row[i] or "").strip()

            # Skip empty cells
            if not current:
                i += 1
                continue

            # Look ahead to see if next cell should be merged
            if i + 1 < len(row):
                next_cell = str(row[i + 1] or "").strip()

                if not next_cell:
                    # Next is empty, just add current
                    merged_row.append(current)
                    i += 1
                    continue

                # Check if this looks like a mid-word split
                # Next cell starts with lowercase = likely continuation
                if next_cell[0].islower():
                    # Check if next cell starts with a preposition (should have space)
                    prepositions = ['of ', 'in ', 'on ', 'at ', 'to ', 'by ', 'for ', 'and ', 'the ']
                    starts_with_preposition = any(next_cell.lower().startswith(prep) for prep in prepositions)

                    # Also check if it's exactly a preposition
                    is_preposition = next_cell.lower() in ['of', 'in', 'on', 'at', 'to', 'by', 'for', 'and', 'the']

                    if starts_with_preposition or is_preposition:
                        # Merge with space
                        merged_row.append(current + " " + next_cell)
                        i += 2
                        continue
                    else:
                        # Not a preposition, merge without space (mid-word)
                        merged_row.append(current + next_cell)
                        i += 2
                        continue

            # No merge, keep as-is
            merged_row.append(current)
            i += 1

        merged_table.append(merged_row)

    return merged_table


def format_table(table):
    """Convert a table to a clean list of lists format."""
    if not table:
        return None

    # Clean and normalize the table
    cleaned = []
    for row in table:
        # Strip whitespace from each cell
        cleaned_row = [str(cell or "").strip() for cell in row]
        # Only keep non-empty rows
        if any(cleaned_row):
            cleaned.append(cleaned_row)

    if not cleaned:
        return None

    # Merge split cells first
    cleaned = merge_split_cells(cleaned)

    # Now find actual column count (max non-empty cells in any row)
    num_cols = max(len(row) for row in cleaned) if cleaned else 0

    # Final cleanup: make sure all rows have consistent length
    # But don't pad with empty strings
    final_table = []
    for row in cleaned:
        # Only keep rows that have content
        if row:
            final_table.append(row)

    return final_table


def find_table_in_passage(passage_text, all_tables):
    """
    Try to match passage text content with extracted tables.
    Returns the best matching table or None.
    """
    if not all_tables:
        return None

    passage_lower = passage_text.lower()

    # Score each table by how well it matches the passage
    best_table = None
    best_score = 0

    for table in all_tables:
        if not table or len(table) < 2:
            continue

        score = 0

        # Get sample cells from the table (check all rows)
        sample_cells = []
        for row in table:
            for cell in row:
                if cell and str(cell).strip() and len(str(cell).strip()) > 2:
                    sample_cells.append(str(cell).strip().lower())

        # Count how many table cells appear in passage
        for cell in sample_cells:
            if cell in passage_lower:
                score += 1

        # Bonus points for header keywords matching
        if table[0]:
            header_text = " ".join(str(cell or "").lower() for cell in table[0])
            header_keywords = ["country", "height", "age", "year", "name", "value", "percent", "title", "author",
                               "pyramid"]
            for kw in header_keywords:
                if kw in header_text and kw in passage_lower:
                    score += 2

        if score > best_score:
            best_score = score
            best_table = table

    # Only return table if we have reasonable confidence (at least 3 matches)
    if best_score >= 3:
        return best_table

    return None


def extract_passage_and_table(passage_raw, all_tables):
    """
    Separate passage text from table content.
    Returns (table_title, formatted_table, passage_text).
    """
    table = find_table_in_passage(passage_raw, all_tables)

    if not table:
        return None, None, passage_raw.strip()

    # Format the table
    formatted_table = format_table(table)

    # Strategy: Find the table in the raw text by looking for header row
    # Everything before = title
    # Everything after = passage

    lines = passage_raw.split('\n')

    # Get the header row (first row of table)
    if table and len(table) > 0:
        header_cells = [str(cell).strip().lower() for cell in table[0] if str(cell).strip()]

        # Find line that contains most header cells
        table_start_idx = None
        table_end_idx = None

        for i, line in enumerate(lines):
            line_lower = line.strip().lower()
            if not line_lower:
                continue

            # Count how many header cells appear in this line
            header_matches = sum(1 for cell in header_cells if cell in line_lower)

            # If this line has most of the header cells, it's the start
            if header_matches >= len(header_cells) * 0.6:
                table_start_idx = i
                break

        # If we found the start, find the end by looking for the last data row
        if table_start_idx is not None:
            # Get cells from last row of table
            last_row_cells = [str(cell).strip().lower() for cell in table[-1] if str(cell).strip()]

            # Search forward from table start
            for i in range(table_start_idx, len(lines)):
                line_lower = lines[i].strip().lower()
                if not line_lower:
                    continue

                # Count matches with last row
                last_row_matches = sum(1 for cell in last_row_cells if cell in line_lower)

                if last_row_matches >= len(last_row_cells) * 0.5:
                    table_end_idx = i

        # Extract title (before table) and passage (after table)
        title_lines = []
        passage_lines = []

        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                continue

            if table_start_idx is not None:
                if i < table_start_idx:
                    # Before table - this is the title
                    title_lines.append(stripped)
                elif table_end_idx is not None and i > table_end_idx:
                    # After table - this is the actual passage
                    passage_lines.append(stripped)
            else:
                # Couldn't find table, treat everything as passage
                passage_lines.append(stripped)

        table_title = " ".join(title_lines) if title_lines else None
        passage_text = " ".join(passage_lines) if passage_lines else ""

        return table_title, formatted_table, passage_text.strip()

    return None, formatted_table, passage_raw.strip()


def split_into_question_blocks(pages):
    """Splits pages into blocks starting with Question ID."""
    blocks = []

    for page_data in pages:
        page_num = page_data["page"]
        text = page_data["text"]
        tables = page_data["tables"]

        # Split by Question ID on this page
        parts = re.split(r"(Question ID\s+[0-9a-f]+)", text, flags=re.I)

        # Pair header with following text
        for i in range(1, len(parts), 2):
            block_text = parts[i] + "\n" + parts[i + 1]
            blocks.append({
                "text": block_text,
                "page": page_num,
                "tables": tables
            })

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

        # Strip trailing junk
        text = re.split(r"(Correct Answer|Rationale|Question ID|ID:|Answer\b)", text, flags=re.I)[0]

        choices.append({
            "label": label,
            "text": clean(text)
        })

    return choices


def extract_metadata(block):
    lines = [ln.strip() for ln in block.splitlines() if ln.strip()]

    # Find the labels line
    label_idx = None
    for i, ln in enumerate(lines):
        if all(x in ln.lower() for x in ["assessment", "test", "domain", "skill", "difficulty"]):
            label_idx = i
            break

    if label_idx is None:
        return {"test": None, "domain": None, "skill": None, "difficulty": None}

    # Collect value lines until ID:
    value_lines = []
    for ln in lines[label_idx + 1:]:
        if ln.startswith("ID:"):
            break
        value_lines.append(ln)

    merged = " ".join(value_lines)
    cols = re.split(r"\s{2,}", merged)
    if len(cols) < 5:
        cols = merged.split()

    test = None
    domain = None
    skill = None

    # Detect "Reading and Writing"
    if "Reading" in cols and "Writing" in cols:
        ri = cols.index("Reading")
        test = "Reading and Writing"
        del cols[ri:ri + 3]

    # Known domains
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

    # Skill
    remaining = []
    for c in cols:
        if set(c) <= set("●○□■▬▮"):
            break
        remaining.append(c)
    skill = " ".join(remaining) if remaining else None

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


def parse_block(block_data):
    """Extracts id, passage, question, choices, correct answer, rationale."""
    block = block_data["text"]
    tables = block_data.get("tables", [])

    q = {}

    # Question ID
    id_match = ID_PATTERN.search(block)
    if not id_match:
        return None
    q["id"] = id_match.group(1)

    meta = extract_metadata(block)
    q["test"] = meta.get("test")
    q["domain"] = meta.get("domain")
    q["skill"] = meta.get("skill")
    q["difficulty"] = meta.get("difficulty")

    # Extract question sentence
    q_sentence = QUESTION_SENTENCE.search(block)
    if q_sentence:
        q["question"] = clean(q_sentence.group(1))
    else:
        q["question"] = ""

    # Extract passage text
    id_line_match = re.search(r"ID:\s*([0-9a-f]{6,})\s*\n", block, re.I)
    passage_start = id_line_match.end() if id_line_match else 0

    if q_sentence:
        passage_raw = block[passage_start: q_sentence.start()]
    else:
        passage_raw = block[passage_start:]

    # Separate table title, table, and passage text
    table_title, table_formatted, passage_text = extract_passage_and_table(passage_raw, tables)

    # Store in order: table_title, table, passage
    q["table_title"] = table_title
    q["table"] = table_formatted
    q["passage"] = passage_text

    # Extract choices
    q["choices"] = parse_choices(block)

    # Extract correct answer
    ans_match = CORRECT_PATTERN.search(block)
    q["correct"] = ans_match.group(1) if ans_match else None

    # Extract rationale
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
    blocks = split_into_question_blocks(pages)

    questions = []
    for b in blocks:
        q = parse_block(b)
        if q:
            questions.append(q)

    return questions


if __name__ == "__main__":
    input_pdf = "SAT Suite Question Bank - Results2.pdf"
    output_json = "parsed_sat_questions2.json"

    results = parse_pdf(input_pdf)

    with open(output_json, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Extracted {len(results)} questions → {output_json}")

    # Show sample with table
    tables_found = [q for q in results if q.get("table")]
    if tables_found:
        print(f"\nFound {len(tables_found)} questions with tables")
        print("\nSample question with table:")
        sample = tables_found[0]
        print(f"ID: {sample['id']}")
        if sample.get('table_title'):
            print(f"\nTable Title: {sample['table_title']}")
        if sample.get('table'):
            print(f"\nTable (list of lists):")
            for row in sample['table']:
                print(f"  {row}")
        if sample.get('passage'):
            print(f"\nPassage: {sample['passage'][:150]}...")
        print(f"\nQuestion: {sample['question'][:100]}...")
    else:
        print("\nNo tables detected in questions")