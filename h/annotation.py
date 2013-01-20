from pyramid_basemodel import Base, Session
from horus.models import BaseModel
from annotator import authz

from sqlalchemy import Column, Integer, String, DateTime, Text, desc
from sqlalchemy.schema import Index
import sqlalchemy.types as types

from flask import current_app, g
import iso8601
import json
import datetime
import uuid

import logging

log = logging.getLogger(__name__)
RESULTS_MAX_SIZE = 200

class JsonString(types.TypeDecorator):
    impl = types.String
    
    def process_bind_param(self, value, dialect):
        return json.dumps(value)
    
    def process_result_value(self, value, dialect):
        if not value : return value
        else : return json.loads(value)

class Annotation(dict):
    class _Model(Base, BaseModel):
        __tablename__ = 'annotations'
        
        id = Column(String, primary_key = True,  autoincrement=True)
        annotator_schema_version = Column(String, default = None)
        created = Column(DateTime(timezone=True), default = None)
        updated = Column(DateTime(timezone=True), default = None, index = True)
        quote = Column(String, default = None)
        tags = Column(String, default = None)
        text = Column(Text, default = None)
        uri = Column(String, default = None, index = True)
        user = Column(String, default = None)
        consumer = Column(String, default = None)
        ranges = Column(JsonString, default = None)
        permissions = Column(JsonString, default=None)
        thread = Column(String, default = None, index = True)
        
        def __dir__(self):
            return ['id','annotator_schema_version','created','updated','quote','tags','text','uri','user','consumer','ranges','permissions','thread']
        
        __mapper_args__ = {
            'version_id_col' : id, 
            'version_id_generator' : lambda version:uuid.uuid4().hex
        }
        
        def __init__(self):
            pass

        def __repr__(self):
            user = '' if self.user is None else self.user
            quote = '' if self.quote is None else self.quote
            return "<Annotation('%s','%s','%s')>" % (self.id, user, quote)
        
        def __json__(self):        
            return ''
        
    def __init__(self, model = None, *args, **kwargs):        
        self.session = Session()
        if model and type(model) == Annotation._Model:
            self.model = model
            for key in dir(model) :
                dict.__setitem__(self, key, getattr(model, key))
        else :             
            self.model = Annotation._Model()
            self.update(model, *args, **kwargs)

    @classmethod
    def update_settings(cls):
        '''This method is called by store.py but it has no relevant meaning here'''
        pass
               
    @classmethod
    def create_all(cls):
        ''' Create_all is automatically handled by the pyramid.basemodel.bind_engine()
            Manual calling is not needed'''
        pass
    
    @classmethod
    def fetch(cls, id):
        try :
            res = cls.session.query(_Model).filter(cls.id == id).one()
        except sqlalchemy.orm.exc.NoResultFound :
            return None
        return res
   
    @classmethod     
    def search(cls, **kwargs):
        q = cls._build_query(**kwargs)
        if not q:
            return []        

        models = q.all()
        res = []
        for model in models:
             res.append(Annotation(model))
        return res

    @classmethod
    def search_raw(cls, request):
        raise Exception('Not supported in this implementation. May add direct SQL query option here.')

    @classmethod
    def count(cls, **kwargs):
        q = cls._build_query(**kwargs)
        if not q:
            return 0
        return q.count()

    def save(self, *args, **kwargs):
        # For brand new annotations
        _add_created(self)
        _add_default_permissions(self)
        # For all annotations about to be saved
        _add_updated(self)
        
        self.session.add(self.model)
        self.session.flush()
        #Write back autocolumns
        dict.__setitem__(self, 'id', self.model.id)

    def delete(self):
        self.session.delete(self)
        self.session.flush()

    @classmethod
    def _build_query(cls, offset=0, limit=20, **kwargs):
        query = Session().query(Annotation._Model)
        
        if kwargs:
            # Add a term query for each keyword
            for k, v in kwargs.iteritems():
                query = query.filter(getattr(Annotation._Model,k) == v)           

        if current_app.config.get('AUTHZ_ON'):
            f = authz.permissions_filter(g.user)
            if not f:
                return False # Refuse to perform the query
            #Not needed: q['query'] = {'filtered': {'query': q['query'], 'filter': f}}
        query = query.order_by(desc('updated'))
        query = query.limit(min(RESULTS_MAX_SIZE, max(0, limit)))
        query = query.offset(max(0, offset))
        return query

    #Customizing Dict to be sync with the _Model
    def update(self, m, *args, **kwargs):
        if m == None : m = {}
        for k, v in dict(m, *args, **kwargs).iteritems():
            self[k] = v
 
    def __setitem__(self, key, value):    
        dict.__setitem__(self, key, value)
        saved_value =  value         
        setattr(self.model, key, saved_value)

    def __delitem__(self, key):
        dict.__delitem__(self, key)
        setattr(self.model, key, None)
        
    def __json__(self):
        res = {}
        for key, value in self.items() :
            res[key] = value
        return res
    
def _add_created(ann):
    if 'created' not in ann:
        ann['created'] = datetime.datetime.now(iso8601.iso8601.UTC)

def _add_updated(ann):
    ann['updated'] = datetime.datetime.now(iso8601.iso8601.UTC)

def _add_default_permissions(ann):
    if 'permissions' not in ann:
        ann['permissions'] = {'read': [authz.GROUP_CONSUMER]}
