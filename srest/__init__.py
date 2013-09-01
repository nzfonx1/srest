from pyramid.config import Configurator
from sqlalchemy import engine_from_config
from .models import initialize_sql
from .models import (
    DBSession,
    Base,
)

#  http://zhuoqiang.me/restful-pyramid.html


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    initialize_sql(engine)
    config = Configurator(settings=settings)
    config.add_static_view('static', 'static', cache_max_age=3600)

    config.add_route('delete_files', '/files', request_method="DELETE", xhr=False)
    config.add_route('postfile', '/files', request_method="POST")
    config.add_route('files', '/files', request_method="GET")

    config.add_route('file', '/files/{name}')
    
    config.add_route('getfile', '/getfile/{name}')
    

    config.scan()
    return config.make_wsgi_app()
