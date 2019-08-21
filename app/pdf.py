import pdftotext
import json
import pprint

def read_pdf(f):
    pdf = pdftotext.PDF(f)
    return "\n\n".join(pdf)

def parse_pdf(text):
    result = {}
    schedule = text[text.find("Teacher\n") + 9:text.find("    Bus")].split("\n")
    del schedule[-1]

    for num, course in enumerate(schedule):
        if "Q1" in course:
            del schedule[num]
            del schedule[num]
            del schedule[num]

        if ("Orch Lab" in course) and (not "Study Hall Orch Lab" in course):
            del schedule[num]

        if ("Financial Literacy" in course) and (not "Study Hall/Financial Literacy" in course):
            del schedule[num]

        teacher_name = course[course.rfind("  ") + 2:]
        result[str(num)] = {"teacher_name": f"{teacher_name}"}

    return result if "Student Schedule" in text else ""
