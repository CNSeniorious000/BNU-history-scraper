from fastapi import FastAPI, Request
from core.people import load, get_all_data
from starlette.templating import Jinja2Templates

app = FastAPI()

try:
    people = load(open("people.pkl", "rb"))
except FileNotFoundError:
    people = get_all_data()


def to_json(name):
    person = people[name]
    result = {"简介": person.introduction, "相关人物": person.relevant_person}
    if person.apartments:
        result["相关机构"] = person.apartments
    if person.subjects:
        result["相关学科"] = person.subjects
    result["相关事件"] = person.events
    return result


@app.get("/person/{name}")
def personal_page(request: Request, name: str):
    return Jinja2Templates(".").TemplateResponse(
        "template.html",
        {
            "request": request,
            "title": name,
            "person": to_json(name)
        }
    )
