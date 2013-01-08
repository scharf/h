from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import create_session, sessionmaker
from sqlalchemy import Column, Integer, String, DateTime, Text, MetaData, desc, create_engine
from sqlalchemy.dialects.postgresql import ARRAY, HSTORE
from sqlalchemy.ext.mutable import MutableDict 

from annotator.jsonencoderregistry import JSONEncoderRegistry

from flask import current_app, g
import iso8601
from annotator import authz
import json
import datetime

import logging

log = logging.getLogger(__name__)
RESULTS_MAX_SIZE = 200

_metadata = MetaData()
##_metadata.bind = 'sqlite:///'
#_metadata.bind = 'postgresql+psycopg2://hypo:hypopwd@localhost/hypodb'
_engine = create_engine('postgresql+psycopg2://hypo:hypopwd@localhost/hypodb')

#_metadata.create_all()

class AlchemyBackend(object):
    session = None
    
    @classmethod
    def getSession(cls):
        if cls.session is None:
            Session = sessionmaker(bind=_engine)
            session = Session()
        return session

class Annotation(dict):
    class _Model(declarative_base()):
        __tablename__ = 'annotations'
        
        id = Column(Integer, primary_key = True)
        annotator_schema_version = Column(String, default = None)
        created = Column(DateTime(timezone=True), default = None)
        updated = Column(DateTime(timezone=True), default = None)
        quote = Column(String, default = None)
        tags = Column(String, default = None)
        text = Column(Text, default = None)
        uri = Column(String, default = None)
        user = Column(String, default = None)
        consumer = Column(String, default = None)
        ranges = Column(String, default = None)
        permissions = Column(String, default=None)
        thread = Column(String, default = None)
        
        stores_json_as_string = ['ranges', 'permissions']

        def __init__(self):
            pass

        def __repr__(self):
            user = '' if self.user is None else self.user
            quote = '' if self.quote is None else self.quote
            return "<Annotation('%s','%s','%s')>" % (self.id, user, quote)
        
        def __dir__(self):
            return ['id','annotator_schema_version','created','updated','quote','tags','text','uri','user','consumer','ranges','permissions','thread']
        
        @classmethod
        def model_json(cls, inst):        
            return ''
        #TODO: Add indexes

    session = AlchemyBackend.getSession()
        
    def __init__(self, model = None, *args, **kwargs):
        if model and type(model) == Annotation._Model:
            log.info('Model constructor')
            self.model = model
            for key in dir(model) :
                if key in Annotation._Model.stores_json_as_string:
                    dict.__setitem__(self, key, json.loads(getattr(model, key)))
                else :
                    dict.__setitem__(self, key, getattr(model, key))
        else :             
            log.info('Normal constructor')
            self.model = Annotation._Model()
            self.model.metadata.create_all(_engine) 
            self.update(model, *args, **kwargs)

    #    @classmethod
    def update_settings(cls):
        pass
        #TODO: implement me
        
    @classmethod
    def create_all(cls):
        pass
        #TODO: implement me
    
    # It would be lovely if this were called 'get', but the dict semantics
    # already define that method name.
    @classmethod
    def fetch(cls, id):
        log.info("Fetch - begin")
        #TODO: expection handling
        return cls.session.query(_Model).filter(cls.id == id).one()
   
    @classmethod     
    def search(cls, **kwargs):
        log.info("Search - begin") 
        #TODO: Normal implementation
        q = cls._build_query(**kwargs)
        if not q:
            return []        

        log.info(str(q))
        models = q.all()
        res = []
        for model in models:
             res.append(Annotation(model))
        log.info('result ' + str(res))
        #TODO: write it normally
        #return q.all()
        return res

    @classmethod
    def search_raw(cls, request):
        log.info("Search raw - begin")
        pass
        #TODO: implement me

    @classmethod
    def count(cls, **kwargs):
        log.info("Count - begin")
        q = cls._build_query(**kwargs)
        if not q:
            return 0
        return q.count()

    def save(self, *args, **kwargs):
        log.info("Save - Begin")
        # For brand new annotations
        _add_created(self)
        _add_default_permissions(self)

        # For all annotations about to be saved
        _add_updated(self)
        
        #self.session.begin()
        self.session.add(self.model)
        self.session.commit()

    @classmethod
    def _build_query(cls, offset=0, limit=20, **kwargs):
        log.info("Build Query - Begin")
        query = cls.session.query(Annotation._Model)
        
        if kwargs:
            # Add a term query for each keyword
            for k, v in kwargs.iteritems():
                 query.filter(k == v)           

        if current_app.config.get('AUTHZ_ON'):
            f = authz.permissions_filter(g.user)
            if not f:
                return False # Refuse to perform the query
            else:
                pass
                #TODO: q['query'] = {'filtered': {'query': q['query'], 'filter': f}}
        query.offset(max(0, offset))
        query.limit(min(RESULTS_MAX_SIZE, max(0, limit)))
        query.order_by(desc('updated'))
        return query

    #Customizing Dict to be sync with the _Model
    def update(self, m, *args, **kwargs):
        if m == None : m = {}
        for k, v in dict(m, *args, **kwargs).iteritems():
            self[k] = v
 
    def __setitem__(self, key, value):    
        dict.__setitem__(self, key, value)
        if key in Annotation._Model.stores_json_as_string:
            #Workaround for strange SQLAlchemy Array Bug / HStore limitation
            saved_value = json.dumps(value)
        else :
            saved_value =  value         
        setattr(self.model, key, saved_value)

    def __delitem__(self, key):
        dict.__delitem__(self, key)
        setattr(self.model, key, None)
        
    #Manual jsoning
    @classmethod
    def to_json(cls, inst):
        res = {}
        for key, value in inst.items() :
            if  key in Annotation._Model.stores_json_as_string :
                res[key] = json.loads(value)
            else :
                res[key] = value
        return res
    
JSONEncoderRegistry.register_json_serializer(Annotation, Annotation.to_json)    
JSONEncoderRegistry.register_json_serializer(Annotation._Model, Annotation._Model.model_json)    
JSONEncoderRegistry.register_json_serializer(datetime.datetime, str)    
        
def _add_created(ann):
    if 'created' not in ann:
        ann['created'] = unicode(datetime.datetime.now(iso8601.iso8601.UTC).isoformat())

def _add_updated(ann):
    ann['updated'] = datetime.datetime.now(iso8601.iso8601.UTC).isoformat()

def _add_default_permissions(ann):
    if 'permissions' not in ann:
        ann['permissions'] = {'read': [authz.GROUP_CONSUMER]}

