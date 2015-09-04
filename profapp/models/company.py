from sqlalchemy import Column, String, ForeignKey, update
from sqlalchemy.orm import relationship, backref
from db_init import Base, db_session
from ..constants.TABLE_TYPES import TABLE_TYPES
from flask import g
from config import Config
from ..constants.STATUS import STATUS
from ..constants.USER_ROLES import COMPANY_OWNER_RIGHTS, RIGHTS
from utils.db_utils import db
from .users import User
from .files import File, FileContent
from .pr_base import PRBase
from sqlalchemy import CheckConstraint
from flask import abort
from db_init import db_session
from functools import reduce
from .rights import Right, ALL_AVAILABLE_RIGHTS_FALSE
from ..controllers.request_wrapers import check_rights
from flask.ext.login import current_user
# from ..models.company import UserCompany


class Company(Base, PRBase):
    __tablename__ = 'company'
    id = Column(TABLE_TYPES['id_profireader'], primary_key=True)
    name = Column(TABLE_TYPES['name'], unique=True)
    logo_file = Column(String(36), ForeignKey('file.id'))
    journalist_folder_file_id = Column(String(36), ForeignKey('file.id'))
    corporate_folder_file_id = Column(String(36), ForeignKey('file.id'))
    portal_consist = Column(TABLE_TYPES['boolean'])
    author_user_id = Column(TABLE_TYPES['id_profireader'],
                            ForeignKey('user.id'),
                            nullable=False)
    country = Column(TABLE_TYPES['name'])
    region = Column(TABLE_TYPES['name'])
    address = Column(TABLE_TYPES['name'])
    phone = Column(TABLE_TYPES['phone'])
    phone2 = Column(TABLE_TYPES['phone'])
    email = Column(TABLE_TYPES['email'])
    short_description = Column(TABLE_TYPES['text'])

    #todo: add company time creation

    owner = relationship('User', backref='companies')
    employees = relationship('User', secondary='user_company', lazy='dynamic')
    logo_file_relationship = relationship('File',
                                          uselist=False,
                                          backref='logo_owner_company',
                                          foreign_keys='Company.logo_file')

    def __init__(self, name=None,
                 portal_consist=False,
                 author_user_id=None,
                 user=current_user,
                 passed_file=None,
                 logo_file=None, country=None, region=None,
                 address=None, phone=None, phone2=None, email=None,
                 short_description=None):
        self.name = name
        self.portal_consist = portal_consist
        self.author_user_id = author_user_id
        self.user = user
        self.logo_file = logo_file
        self.country = country
        self.region = region
        self.address = address
        self.phone = phone
        self.phone2 = phone2
        self.email = email
        self.short_description = short_description

        # get all users in company : company.employees
        # get all users companies : user.employers

        if author_user_id:
            user = db_session.querry(User).get(author_user_id)
            user_id = author_user_id
        else:
            user_id = user.get_id()

        if passed_file:
            file = File(company_id=self.id,
                        parent_id=self.corporate_folder_file_id,
                        author_user_id=user_id,
                        name=passed_file.filename,
                        mime=passed_file.content_type)

            file_content = FileContent(file_content=file,
                                       content=passed_file.stream.read(-1))
            file.file_all_content = file_content
            self.logo_file_relationship = file
            user.files.all().append(file)

        user_company = UserCompany(status=STATUS.ACTIVE(),
                                   rights=COMPANY_OWNER_RIGHTS)
        user_company.employer = self
        user.employer_assoc.append(user_company)  # .all() added
        user.companies.append(self)

        db_session.merge(user)
        db_session.commit()

    @staticmethod
    def query_company(company_id):
        ret = db(Company, id=company_id).one()
        return ret

    @staticmethod
    def search_for_company(user_id, searchtext):
        query_companies = db(Company).\
            filter(Company.name.like("%"+searchtext+"%")).all()
        ret = []
        for x in query_companies:
            ret.append(x.dict())

        return ret
        # return PRBase.searchResult(query_companies)

    @staticmethod
    def update_comp(company_id, data, passed_file):

        comp = db(Company, id=company_id)
        upd = {x: y for x, y in zip(data.keys(), data.values())}
        comp.update(upd)

        if passed_file:
            file = File(company_id=company_id,
                        parent_id=comp.one().corporate_folder_file_id,
                        author_user_id=g.user_dict['id'],
                        name=passed_file.filename,
                        mime=passed_file.content_type)
            comp.update(
                {'logo_file':
                    file.upload(content=passed_file.stream.read(-1)).id}
            )

        db_session.flush()

    # @staticmethod
    # def query_employee(comp_id):
    #
    #     employee = db(UserCompany, company_id=comp_id,
    #                   user_id=g.user_dict['id']).first()
    #     return employee or False

    def query_owner_or_member(self, company_id):
        employee = self.query_employee(company_id)
        return True if employee and employee.status == STATUS().ACTIVE() else \
            False


def simple_permissions(set_of_rights):  # .p(right_name)
    def lambda_function(**kwargs):
        if 'company_id' in kwargs.keys():
            company_object = kwargs['company_id']
        elif 'company' in kwargs.keys():
            company_object = kwargs['company']
        else:
            company_object = None
        if 'user_id' in kwargs.keys():
            user_object = kwargs['user_id']
        elif 'user' in kwargs.keys():
            user_object = kwargs['user']
        else:
            user_object = None
        return UserCompany.permissions(user_object,
                                       company_object,
                                       set_of_rights)
    return {set_of_rights: lambda_function}


class UserCompany(Base, PRBase):
    __tablename__ = 'user_company'

    id = Column(TABLE_TYPES['id_profireader'], primary_key=True)
    user_id = Column(TABLE_TYPES['id_profireader'],
                     ForeignKey('user.id'),
                     primary_key=True)
    company_id = Column(TABLE_TYPES['id_profireader'],
                        ForeignKey('company.id'),
                        primary_key=True)
    status = Column(TABLE_TYPES['id_profireader'])
    md_tm = Column(TABLE_TYPES['timestamp'])
    rights = Column(TABLE_TYPES['bigint'],
                    CheckConstraint('rights >= 0', name='unsigned_rights'))

    employer = relationship('Company', backref='employee_assoc')
    employee = relationship('User',
                            backref=backref('employer_assoc', lazy='dynamic'))

    # todo: check handling md_tm

    def __init__(self, user_id=None, company_id=None, status=None, rights=0):
        self.user_id = user_id
        self.company_id = company_id
        self.status = status
        self.rights = rights

    @staticmethod
    def user_in_company(user_id, company_id):
        ret = db(UserCompany, user_id=user_id, company_id=company_id).one()
        return ret

    # do we provide any rights to user at subscribing?
    def subscribe_to_company(self):
        user = User.user_query(self.user_id)
        company = db(Company, id=self.company_id).one()
        user.employers.append(company)
        company.employee.append(user)
        self.save()

    @staticmethod
    def suspend_employee(comp_id, user_id):
        db(UserCompany, company_id=comp_id, user_id=user_id).\
            update({'status': STATUS.SUSPEND()})
        db_session.flush()

    @staticmethod
    def apply_request(comp_id, user_id, bool):
        if bool == 'True':
            stat = STATUS().ACTIVE()
            UserCompany.update_rights(user_id,
                                      comp_id,
                                      Config.BASE_RIGHT_IN_COMPANY)
        else:
            stat = STATUS().REJECT()
        db(UserCompany, company_id=comp_id, user_id=user_id,
           status=STATUS().NONACTIVE()).update({'status': stat})
        db_session.flush()

    ## corrected
    @check_rights(*simple_permissions(frozenset()))
    def update_rights(self, user, company, new_rights):
        new_rights_binary = Right.transform_rights_into_integer(new_rights)
        user_comp = db(UserCompany, user_id=user.id, company_id=company.id)
        rights_dict = {'rights': new_rights_binary}
        user_comp.update(rights_dict)

    #  corrected
    @staticmethod
    def show_rights(comp_id):
        emplo = {}
        for x in db(Company, id=comp_id).one().employees:
            user_in_company = UserCompany.user_in_company(user_id=x.id,
                                                          company_id=comp_id)
            emplo[x.id] = {'id': x.id,
                           'name': x.user_name,
                           'user': x,
                           'rights': set(),
                           'companies': [x.employers],
                           'status': user_in_company.status,
                           'date': user_in_company.md_tm}

            emplo[x.id]['rights'] = \
                Right.transform_rights_into_set(user_in_company.rights)
            # earlier it was a dictionary:
            # {'right_1': True, 'right_2': False, ...}
        return emplo

    # it is correct
    @staticmethod
    def suspended_employees(comp_id):
        suspended_employees = {}
        for x in Company.query_company(comp_id).employees:
            user_in_company = UserCompany.user_in_company(user_id=x.id,
                                                          company_id=comp_id)
            if user_in_company.status == STATUS.SUSPEND():
                suspended_employees[x.id] = x.id
                suspended_employees[x.id] = {'name': x.user_name,
                                             'user': x,
                                             'companies': [x.employers],
                                             'date': user_in_company.md_tm}
        return suspended_employees

    @staticmethod
    def permissions(user_object, company_object, needed_rights_iterable):
        if not (user_object and company_object):
            return True
        user = user_object
        company = company_object
        if type(user_object) is int:
            user = db_session.query(User).filter_by(id=user_object).first()
        if type(company_object) is int:
            company = db_session.query(Company).\
                filter_by(id=company_object).first()

        needed_rights_int = \
            Right.transform_rights_into_integer(needed_rights_iterable)

        available_rights = \
            [user_company.rights for user_company in user.employers
             if user_company.company == company
             ][0] or 0

        if available_rights & needed_rights_int != needed_rights_int:
            return abort(403)
        else:
            return True
