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
            course = course.replace("Orch Lab", "Study Hall/Orch Lab")

        if ("Financial Literacy" in course) and (not "Study Hall/Financial Literacy" in course):
            del schedule[num]
            course = course.replace("Financial Literacy", "Study Hall/Financial Literacy")

        teacher_name = course[course.rfind("  ") + 2:]
        course = " ".join(course.split())
        period = course[:2]
        course_name = course[2:(course.find("FY") if "FY" in course else course.find("Q1")) - 1]
        result[str(num)] = {"period": f"{period}", "course_name": f"{course_name}", "teacher_name": f"{teacher_name}"}

    return result

if __name__ == "__main__":
    with open("/tmp/uploads/rahul.pdf", "rb") as f:
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(parse_pdf(read_pdf(f)))
