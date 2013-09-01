import unittest
import requests
import urlparse
import simplejson

BASE_URL = 'http://localhost:9000/'


def request(method, path, **kw):
    url = urlparse.urljoin(BASE_URL, path)
    response = requests.request(method, url, **kw)

    try:
        json = response.json()
    except simplejson.JSONDecodeError:
        json = {}
    return response.status_code, json


def upload_file(filename, fileobj):
    files = {'file': (filename, fileobj)} if filename else {}
    return request('POST', 'files', files=files)


class AppTestCase(unittest.TestCase):
    def setUp(self):
        request('DELETE', '/files')


class TestUpload(AppTestCase):

    def call_FUT(self, filename, fileobj):
        return upload_file(filename, fileobj)

    def test_missing_file(self):
        self.assertEqual(self.call_FUT(None, None),
                         (400, {}))

    def test_file_with_no_content(self):
        self.assertEqual(self.call_FUT('test', ''),
                         (400, {}))

    def test_file_size_info(self):
        status, info = self.call_FUT('test2', '12345')
        self.assertEqual(status, 201)
        self.assertEqual(info['file_size'], 5)

    def test_file_name_info(self):
        status, info = self.call_FUT('testing-this.txt', 'just text')
        self.assertEqual(status, 201)
        self.assertEqual(info['file_name'], 'testing-this.txt')

    def test_file_content_type(self):
        status, info = self.call_FUT('test.txt', 'just text')
        self.assertEqual(status, 201)
        self.assertEqual(info['file_type'], 'text/plain')

    def test_unknown_file_content_type(self):
        status, info = self.call_FUT('xyz', '\xDE\xAD\xBE\xEF')
        self.assertEqual(status, 201)
        self.assertEqual(info['file_type'], 'text/plain')

    def test_file_metadata(self):
        status, info = self.call_FUT('some file.txt', 'testing')
        self.assertEqual(status, 201)
        self.assertTrue(info['id'])
        self.assertTrue(info['file_name'])
        self.assertTrue(info['file_size'])
        self.assertTrue(info['file_type'])
        self.assertTrue(info['download_url'])

    def test_file_download(self):
        status, info = self.call_FUT('some file.txt', 'testing')
        self.assertEqual(status, 201)
        download_url = info['download_url']
        response = requests.get(download_url)
        self.assertEqual(response.status_code, 200)
        content_type = response.headers['content-type'].split(';')[0]
        self.assertEqual(content_type, 'text/plain')


class TestFileInfo(AppTestCase):

    def call_FUT(self, file_id=None):
        if not file_id:
            status, info = upload_file('test.jpg', 'some file data')
            self.assertEqual(status, 201)
            file_id = info['id']
        return request('GET', '/files/%s' % file_id)

    def test_it_works(self):
        status, info = self.call_FUT()
        self.assertEqual(status, 200)
        self.assertEqual(info['file_type'], 'text/plain')
        self.assertEqual(info['file_size'], 14)

    def test_file_not_found(self):
        status, info = self.call_FUT(6283)
        self.assertEqual(status, 404)


class TestFileIndex(AppTestCase):

    def call_FUT(self):
        return request('GET', '/files')

    def test_empty_index(self):
        request('DELETE', '/files')
        status, files = self.call_FUT()
        self.assertEqual(status, 200)
        self.assertEqual(files, [])

    def test_creation_order(self):
        upload_file('1st file', 'test')
        upload_file('2nd file', 'testing')

        status, files = self.call_FUT()
        self.assertEqual(status, 200)
        self.assertEqual(len(files), 2)

        self.assertEqual(files[0]['file_name'], '2nd file')
        self.assertEqual(files[1]['file_name'], '1st file')


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        BASE_URL = sys.argv.pop()

    unittest.main()
