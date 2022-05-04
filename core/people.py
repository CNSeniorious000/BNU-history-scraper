from requests import get
from loguru import logger
from pickle import dump, load
from bs4 import BeautifulSoup
from collections import deque
from pydantic import BaseModel
from functools import cached_property


class PersonPage:
    def __init__(self, name):
        self.name = name
        self.url = "http://bnu.hiwis.com/People/People_Detail?" \
                   f"keyword={name}"

    __str__ = __repr__ = lambda self: f"PersonPage({self.name})"

    @cached_property
    def html(self):
        logger.info(f"getting {self.url}")
        return BeautifulSoup(get(self.url).text, "lxml")

    @cached_property
    def jpg(self):
        logger.info(f"downloading image of {self.name}")
        return get(f"http://bnu.hiwis.com/images/{self.name}.jpg").content

    def show_image(self):
        from cv2 import imshow, waitKey
        from imageio import imread
        imshow(str(self.name), imread(self.jpg)[..., ::-1])
        return waitKey(18)

    @cached_property
    def relevant_person(self):
        logger.info(f"finding related people of {self.name}")
        return [li.a.text for li in self.html.section.find_all("div")[3].ul if li.name == "li"]

    @cached_property
    def introduction(self):
        logger.info(f"finding introduction of {self.name}")
        return self.html.section.find_all("div")[2].text.strip()

    @cached_property
    def apartments(self):
        logger.info(f"finding apartments of {self.name}")
        for h2 in self.html.section.find_all("h4"):
            if h2.text == "相关机构":
                h2: BeautifulSoup
                return h2.find_next_sibling().text.split()
        return []

    @cached_property
    def subjects(self):
        logger.info(f"finding subjects of {self.name}")
        for h2 in self.html.section.find_all("h4"):
            if h2.text == "相关学科":
                h2: BeautifulSoup
                return h2.find_next_sibling().text.split()
        return []

    @cached_property
    def events(self):
        elements = []
        for element in self.html.section.find_all("div")[-1].dl:
            if element.name == "dt":
                elements.append((element.text, []))
            elif element.name == "dd":
                elements[-1][1].append(element.text)
        return dict(elements)

    @property
    def data(self):
        return Person(name=self.name, url=self.url, jpg=self.jpg, relevant_person=self.relevant_person,
                      introduction=self.introduction, apartments=self.apartments, subjects=self.subjects,
                      events=self.events)


class Person(BaseModel):
    name: str
    url: str
    jpg: bytes
    relevant_person: list[str]
    introduction: str
    apartments: list[str]
    subjects: list[str]
    events: dict[str, list[str]]

    show_image = PersonPage.show_image


def get_all_data(start_name="启功"):
    queue = deque([start_name])
    people = {}

    while queue:
        name = queue.popleft()
        if name in people:
            logger.warning(name)
        else:
            logger.debug(f">>> {name = } >>> {len(queue) = }")
            person = PersonPage(name)
            people[name] = person.data
            queue.extend([i for i in person.relevant_person if i not in queue and i not in people])

    dump(people, open("people.pkl", "wb"))
    return people


def show_all_data():
    try:
        people = load(open("people.pkl", "rb"))
    except FileNotFoundError:
        people = get_all_data()

    for name, person in people.items():
        person: PersonPage
        print(f"{name} has {len(person.events)} events")
        print(f"{name} has {len(person.relevant_person)} related people")
        print(f"{name} has {len(person.apartments)} apartments")
        print(f"{name} has {len(person.subjects)} subjects")
        person.show_image()


if __name__ == '__main__':
    from ctypes import windll

    windll.user32.SetProcessDPIAware(2)

    show_all_data()
