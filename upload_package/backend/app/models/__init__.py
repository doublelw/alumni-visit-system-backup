"""
数据库模型
"""

from .user import User
from .alumni_profile import AlumniProfile
from .visit_application import VisitApplication
from .face_data import FaceData
from .visit_record import VisitRecord
from .target_person import TargetPerson
from .school_calendar import SchoolCalendar, EventBooking

__all__ = ['User', 'AlumniProfile', 'VisitApplication', 'FaceData', 'VisitRecord', 'TargetPerson', 'SchoolCalendar', 'EventBooking']