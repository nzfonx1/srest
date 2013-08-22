from pyramid.response import (Response, FileResponse)
from pyramid.view import view_config
from sqlalchemy.exc import DBAPIError
import os
import uuid
import magic
from .models import (
    DBSession,
    MyModel,
)


@view_config(route_name='getfile', request_method='GET')
def getfile(request):
    """
    GET metadata from DB, fetch file and serve it to the client
    TODO: implement nice error handling
    """

    # get filename from url
    filename = request.matchdict['name']
    session = DBSession()
    # fetch metadata for this file
    result = session.query(MyModel).filter_by(id=filename)

    if result.count() < 1:
        request.response.status = 404
        return {}
    elif result.count() == 1:
        res = result.first()
        filepath = res.path
        response = FileResponse(
            filepath,
            request=request,
            content_type=str(res.filetype)
        )
        return response

    # TODO: handle error
    request.response.status = 404
    return {}


@view_config(route_name='file', request_method='GET', renderer='json')
def getfilemeta(request):
    """
    GET metadata belonging to the specified file
    """

    # get filename from url
    filename = request.matchdict['name']
    session = DBSession()
    # go look for metadata about this filename
    result = session.query(MyModel).filter_by(id=filename)

    if result.count() < 1:
        request.response.status = 404
        return {}
    # there should be only one file
    elif result.count() == 1:
        res = result.first()
        return {'id': res.id, 'file_name': res.name,
                'file_type': res.filetype,
                'file_size': res.size,
                # 'uploader': res.uploader,
                # 'timestamp': str(res.timestamp),
                'download_url': '/getfile/%s' % res.id
                }

    # default to NotFound...
    request.response.status = 404
    return {}


@view_config(route_name='postfile', request_method='POST', renderer='json')
def post_file(request):
    """
    Upload a file
    TODO: abstract method to isolate it so that is possible to scale by adding
     some messaging/queing etc to speed up
    """
    # get filelist
    try:
        fileslist = request.POST.get('file')

        # this is for multiple uploads (could be a new feature)
        # filelist = request.POST.getall('myfile')
        # print ("My files listing: ", fileslist)
        # for f in fileslist:
        #     print ( "individual files: ", f )

        #  get orig filename
        filename = request.POST['file'].filename

        # actual file
        rawfile = request.POST['file'].file
    except:
        request.response.status = 400
        return {}

    # get a uuid for this file
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

    filetype = None
    try:
        filetype = magic.from_file(temp_file_path, mime=True)
    except:  # dont remember how magic handles errors
        pass

    # move file to storage
    os.rename(temp_file_path, filepath)

    # store path and metadata
    session = DBSession()
    # get filesize
    size = os.path.getsize(filepath)

    if size == 0:
        request.response.status = 400
        return {}
    # get uploader address
    uploader = request.remote_addr

    # instantiate a new file
    myfile = MyModel(id="%s" % myuuid4, name=filename,
                     filetype=filetype, path=filepath,
                     size=size, uploader=uploader)
    # store metadata to db
    session.add(myfile)
    session.flush()

    # HTTP: created
    request.response.status = 201
    return {'id':  '%s' % (str(myuuid4)), 'file_type': filetype,
            'download_url': 'http://localhost:9000/getfile/%s' % (str(myuuid4)),
            'file_name': filename, 'file_size': size}


@view_config(route_name='delete_files', renderer='json')
def delete_files(request):
    """
    DELETE all the files
    TODO change this to a loop..cycle, delete each file (both db and fs!)
    """
    try:
        session = DBSession()
        session.query(MyModel).delete()
        # HTTP: OK
        request.response.status = 200
    except:
        # TODO: Handle error
        request.response.status = 500
        return {}
    return {}


@view_config(route_name='files', request_method='GET', renderer='json')
def list_files(request):
    """
    LIST all the files uploaded in the last 5 hours

    """
    from sqlalchemy.sql.expression import between
    from datetime import datetime, timedelta
    session = DBSession()
    now = datetime.now()

    # timeframe could be selectable from an interface for instance
    # easy to implement: analyze pars or set default if missing...
    timeframe = {'hours': 5, 'minutes': 0, 'seconds': 0}
    delta = now - timedelta(**timeframe)
    result = session.query(MyModel)\
        .filter(between(MyModel.timestamp, delta, now))\
        .order_by(MyModel.timestamp.desc())

    if result.count() > 0:
        files = []
        for res in result:
            print res.path
            files.append({'id': res.id,
                          'file_name': res.name,
                          'file_size': res.size,
                          'file_type': res.filetype,
                          'download_url': 'http://localhost:9000/getfile/%s' % res.id
                          })
        return files
    else:
        # Could add a No Content (204) response
        return []

