from pyramid.response import Response
from pyramid.view import view_config
from sqlalchemy.exc import DBAPIError
import os
import uuid
from .models import (
    DBSession,
    MyModel,
)


FILES = {
    'id1': {
        'name': 'file1name',
        'size': 'file1size',
        'date': 'file1date'
    },
    'id2': {
        'name': 'file2name',
        'size': 'file2size',
        'date': 'file2date'
    }
}


@view_config(route_name='file', request_method='GET', renderer='json')
def get_file(request):
    print "GETTING FILE!!"
    name = request.matchdict['name']
    return {'ok': 'ok'}
    # return FILES[name]


@view_config(route_name='postfile', request_method='POST', renderer='json')
def post_file(request):
    print "POSTING FILE!!"
    # name = request.matchdict['name']

    # get filelist
    fileslist = request.POST.get('myfile')

    # this is for multiple uploads (could be a new feature)
    # print ("My files listing: ", fileslist)
    # for f in fileslist:
    #     print ( "individual files: ", f )

    #  get orig filename
    filename = request.POST['myfile'].filename

    # actual file
    rawfile = request.POST['myfile'].file

    myuuid4 = uuid.uuid4()
    filepath = os.path.join('/tmp', '%s' % myuuid4)
    print filepath
    print filename
    temp_file_path = filepath + '~'
    ofile = open(temp_file_path, 'wb')

    # write temp file
    rawfile.seek(0)
    while True:
        data = rawfile.read(2 << 16)
        if not data:
            break
        ofile.write(data)

    #  flush it
    ofile.close()

    # Now that we know the file has been fully saved to disk move it into
    # place.

    os.rename(temp_file_path, filepath)

    # store path and metadata
    session = DBSession()
    size = os.path.getsize(filepath)
    myfile = MyModel(id="%s" % myuuid4, path=filepath, size=size)
    session.add(myfile)
    session.flush()

    return {'error': 0, 'msg': '%s saved successfully' % (filename)}
    # return FILES[name]


@view_config(route_name='files', request_method='GET', renderer='json')
def list_files(request):
    return FILES




# @view_config(route_name='home', renderer='templates/mytemplate.pt')
# def my_view(request):
#     try:
#         one = DBSession.query(MyModel).filter(MyModel.name == 'one').first()
#     except DBAPIError:
#         return Response(conn_err_msg, content_type='text/plain', status_int=500)
#     return {'one': one, 'project': 'srest'}

# conn_err_msg = """\
# Pyramid is having a problem using your SQL database.  The problem
# might be caused by one of the following things:

# 1.  You may need to run the "initialize_srest_db" script
#     to initialize your database tables.  Check your virtual
#     environment's "bin" directory for this script and try to run it.

# 2.  Your database server may not be running.  Check that the
#     database server referred to by the "sqlalchemy.url" setting in
#     your "development.ini" file is running.

# After you fix the problem, please restart the Pyramid application to
# try it again.
# """
