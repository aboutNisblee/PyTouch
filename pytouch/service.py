from pkg_resources import resource_stream, resource_listdir
import logging
from lxml import etree
from pytouch.model import session_scope, Session
from pytouch.model.course import Course, Lesson


class CourseService(object):
    RESOURCE = 'pytouch.resources.courses'
    _schema = etree.XMLSchema(etree.parse(resource_stream(RESOURCE, 'course.xsd')))
    _course_file_names = (f for f in resource_listdir(RESOURCE, '') if f.endswith('.xml'))

    @staticmethod
    def _parse_lesson(lesson_element):
        id = lesson_element.find('id').text
        title = lesson_element.find('title').text
        new_chars = lesson_element.find('newCharacters').text
        text = lesson_element.find('text').text

        return Lesson(uuid=id, title=title, new_chars=new_chars, builtin=True, text=text)

    @staticmethod
    def _parse_course(course_element):
        id = course_element.find('id').text
        title = course_element.find('title').text
        description = course_element.find('description').text
        keyboard_layout = course_element.find('keyboardLayout').text

        course = Course(uuid=id, title=title, description=description, builtin=True, keyboard_layout=keyboard_layout)

        lessons_element = course_element.find('lessons')
        for lesson_element in lessons_element.iter('lesson'):
            course.lessons.append(CourseService._parse_lesson(lesson_element))

        return course

    @classmethod
    def _parse_courses(cls):
        for filename in cls._course_file_names:
            with resource_stream(cls.RESOURCE, filename) as file:
                xml = etree.parse(file)
                if cls._schema.validate(xml):
                    logging.debug('Validated file: {}'.format(file.name))
                    yield cls._parse_course(xml.getroot())
                else:
                    logging.warning('Unable to validate file: {}'.format(file.name))
                    continue

    @staticmethod
    def init_courses():
        with session_scope() as session:
            for course in CourseService._parse_courses():
                session.add(course)

    @staticmethod
    def find_lesson(uuid):
        return Session().query(Lesson).filter(Lesson.uuid == uuid).first()
