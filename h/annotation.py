from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import create_session, sessionmaker
from sqlalchemy import Column, Integer, String, DateTime, Text, desc, create_engine
from sqlalchemy.schema import Index
#from sqlalchemy.dialects.postgresql import ARRAY, HSTORE
#from sqlalchemy.ext.mutable import MutableDict 

from annotator.jsonencoderregistry import JSONEncoderRegistry

from flask import current_app, g
import iso8601
from annotator import authz
import json
import datetime

import logging

log = logging.getLogger(__name__)
RESULTS_MAX_SIZE = 200

#_engine = create_engine('postgresql+psycopg2://hypo:hypopwd@localhost/hypodb')

class AlchemyBackend(object):
    engine = None
    Session = None
    
    @classmethod
    def configure(cls, connect_url):
        cls.engine = create_engine(connect_url)
        cls.Session = sessionmaker(bind = cls.engine)
        
    @classmethod
    def getEngine(cls):
        if cls.engine :return cls.engine
        else: raise Exception("Engine is not initialized yet!")
    
    @classmethod
    def getSession(cls):
        if cls.Session : return cls.Session()
        else: raise Exception("Engine is not initialized yet!")        

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
        
        #TODO: Add Indexes?
                
        stores_json_as_string = set(['ranges', 'permissions'])

        def __dir__(self):
            return ['id','annotator_schema_version','created','updated','quote','tags','text','uri','user','consumer','ranges','permissions','thread']
        
        def __init__(self):
            pass

        def __repr__(self):
            user = '' if self.user is None else self.user
            quote = '' if self.quote is None else self.quote
            return "<Annotation('%s','%s','%s')>" % (self.id, user, quote)
        
        @classmethod
        def model_json(cls, inst):        
            return ''
        
    def __init__(self, model = None, *args, **kwargs):        
        self.session = AlchemyBackend.getSession()
        if model and type(model) == Annotation._Model:
            self.model = model
            for key in dir(model) :
                if key in Annotation._Model.stores_json_as_string:
                    dict.__setitem__(self, key, json.loads(getattr(model, key)))
                else :
                    dict.__setitem__(self, key, getattr(model, key))
        else :             
            self.model = Annotation._Model()
            self.model.metadata.create_all(AlchemyBackend.getEngine()) 
            self.update(model, *args, **kwargs)

    #    @classmethod
    def update_settings(cls):
        pass
        #TODO: implement me
        
    @classmethod
    def create_all(cls):
        pass
        #TODO: implement me
    
    @classmethod
    def fetch(cls, id):
        try :
            res = cls.session.query(_Model).filter(cls.id == id).one()
        except sqlalchemy.orm.exc.NoResultFound :
            return None
        return res
   
    @classmethod     
    def search(cls, **kwargs):
        #TODO: Normal implementation
        q = cls._build_query(**kwargs)
        if not q:
            return []        

        models = q.all()
        res = []
        for model in models:
             res.append(Annotation(model))
        #TODO: write it normally
        return res

    @classmethod
    def search_raw(cls, request):
        pass
        #TODO: implement me

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
        self.session.commit()

    @classmethod
    def _build_query(cls, offset=0, limit=20, **kwargs):
        query = AlchemyBackend.getSession().query(Annotation._Model)
        
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

