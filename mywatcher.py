#-*- coding: utf-8 -*-
import time
import requests
from json import loads
from os import getcwd
from os.path import exists
from watchdog.observers import Observer 
from watchdog.events import FileSystemEventHandler 
from logger import logger

class MyWatcher: 
    # Set the directory on watch 
    def __init__(self, handler=None, watchDirectory = '.'):
        self.watchDirectory = watchDirectory
        self.handler = handler

    def set_handler(self, handler):
        self.handler = handler

    #Estabilish and start thread
    def start(self):
        if self.handler is None:
            return False

        self.observer = Observer() 
        self.observer.schedule(self.handler, self.watchDirectory, recursive=True) 
        self.observer.start()

    def stop(self):
        self.observer.stop()
        self.observer.join()

class MyHandler(FileSystemEventHandler): 
    def __init__(self, wd):
        self.wd = wd

    def check_data(self):
        if 'files' not in self.__dict__:
            self.get_file_data()

    def get_file_data(self):
        ids = []
        files = {
            '': {
                'folder': 'True',
                'id': self.wd.execute_script('return window._ide.fileTreeManager.$scope.rootFolder')['id']
            }
        }

        def folder_rec(ele, path):
            file_entities = ele.find_elements_by_tag_name('file-entity')
            if len(file_entities) == 0:
                return

            for entity in file_entities:
                is_folder = '==' in entity.find_elements_by_tag_name('div')[0].get_attribute('ng-if')
                is_searched = entity.id in ids
                if not(is_searched):
                    ids.append(entity.id)
                    if is_folder:
                        _path = path + entity.find_elements_by_tag_name('span')[0].get_attribute('innerText').strip() + '/'
                        _id = entity.find_elements_by_class_name('ng-isolate-scope')[0].get_attribute('data-target').split('menu-')[1]
                        files.update({
                            _path: {
                                'folder': True,
                                'id': _id
                            }
                        })
                        folder_rec(entity, _path)
                    else:
                        _path = path + entity.find_elements_by_tag_name('span')[0].get_attribute('innerText').strip()
                        _id = entity.find_elements_by_class_name('ng-isolate-scope')[0].get_attribute('data-target').split('menu-')[1]
                        files.update({
                            _path: {
                                'folder': False,
                                'id': _id
                            }
                        })

        folder_rec(self.wd, '')
        self.files = files
        return files

    def expand_folder(self):
        wd = self.wd
        #expand all of the folder
        for item in wd.find_elements_by_tag_name('i'): 
            if 'fa-angle-right' in item.get_attribute('class'): 
                item.click()

    def get_request_meta(self):
        wd = self.wd
        headers = {
            'Host': wd.execute_script('return window.location.hostname')
        }
        cookies = {
            cookie['name']: cookie['value'] for cookie in wd.get_cookies()
        }
        csrf = wd.execute_script('return window.csrfToken')
        return headers, cookies, csrf

    def create_single_folder(self, name, path):
        path += '' if len(path) == 0 or path[-1] == '/' else '/'
        self.check_data()
        parent_folder_id = self.files[path]['id']

        wd = self.wd
        url = wd.current_url
        create_url = url + '/folder'
        headers, cookies, csrf = self.get_request_meta()

        data = {
            'name': name,
            'parent_folder_id': parent_folder_id,
            '_csrf': csrf
        }

        text = requests.post(create_url, data=data, headers=headers, cookies=cookies).text
        try:
            json = loads(text)
        except:
            logger.error('Failed to parse json when creating folder "{}", with text "{}"'.format(name, text))
            return

        logger.info(json)

        if json.get('_id', ''):
            self.files.update({
                path + name + '/': {
                    'folder': True,
                    'id': json['_id']
                }
            })
            #logger.info(self.files)
            logger.info('Created folder "{}" successfully'.format(name))
        else:
            logger.error('Failed to create folder "{}".'.format(name))
            logger.error('data = {}'.format(str(data)))
            logger.error('text = {}'.format(text))

    def create_folder(self, full_path):
        self.check_data()
        path_parts = full_path.split('/')
        for i in range(0, len(path_parts)):
            if '/'.join(path_parts[:i + 1]) not in self.files:
                self.create_single_folder(path_parts[i], '/'.join(path_parts[:i]))

    def upload_file(self, fullpath):
        wd = self.wd
        self.check_data()
        '''
        self.expand_folder()

        #Entering edit mode
        _id = self.files[fullpath]['id']
        item = wd.find_elements_by_xpath('//div[@data-target ="context-menu-{}"]'.format(_id))[0]
        item.click()

        #Modify file
        with open(fullpath, 'r') as rf:
            wd.execute_script('ace.edit("editor").setValue("{}")'.format(rf.read()))
        '''
        name = fullpath.split('/')[-1]
        path = '/'.join(fullpath.split('/')[:-1])
        path += '' if len(path) == 0 or path[-1] == '/' else '/'

        if path not in self.files:
            self.create_folder(path)

        #Prepare data
        headers, cookies, csrf = self.get_request_meta()
        parent_folder_id = self.files[path]['id']
        _csrf = csrf
        url = wd.current_url + '/upload?folder_id={}&_csrf={}&qqfilename={}'.format(parent_folder_id, _csrf, name)

        with open(fullpath, 'rb') as rf:
            files = {
                'qqfile': rf
            }
            text = requests.post(url, headers=headers, cookies=cookies, files=files).text
            #log(headers)
            #log(cookies)
            #log(url)
            try:
                json = loads(text)
                if json['success']:
                    self.files.update({
                        path + name: {
                            'folder': True,
                            'id': json['entity_id']
                        }
                    })
                    logger.info('Uploaded file "{}" successfully'.format(fullpath))
                    for i in range(3):
                        try:
                            ele = wd.find_elements_by_xpath('//button[@ng-click = "done()"]')
                            if len(ele):
                                ele[0].click()
                            ele = wd.find_elements_by_xpath('//a[@ng-click = "recompile()"]')
                            if len(ele):
                                ele[0].click()
                            time.sleep(1)
                        except:
                            pass
                else:
                    logger.info('Failed to upload file "{}".'.format(fullpath))
                    logger.info('url = {}'.format(url))
                    logger.error('text = {}'.format(text))
            except:
                logger.error('Failed to parse json when uploading file "{}"'.format(fullpath))
                logger.error('url = {}'.format(url))
                logger.error('text = {}'.format(text))
                return

    #Move from /old/path/file /new/path/
    def move(self, oldpath, newpath, new_try=False):
        wd = self.wd
        self.check_data()
        headers, cookies, csrf = self.get_request_meta()

        if oldpath not in self.files:
            logger.error('Failed to move file "{}", as source path "{}" doesn\'t exists.'.format(oldpath, oldpath))
            return

        if newpath not in self.files:
            logger.error('Failed to move file "{}", as target path "{}" doesn\'t exists.'.format(oldpath, newpath))

        old_id = self.files[oldpath]['id']
        new_id = self.files[newpath]['id']
        is_folder = self.files[oldpath]['folder']
        if is_folder:
            move_url = wd.current_url + '/folder/' + old_id + '/move'
        else:
            if oldpath.split('/')[-1].split('.')[-1] == 'tex':
                move_url = wd.current_url + '/doc/' + old_id + '/move'
                if new_try:
                    move_url = wd.current_url + '/file/' + old_id + '/move'
            else:
                move_url = wd.current_url + '/file/' + old_id + '/move'
                if new_try:
                    move_url = wd.current_url + '/doc/' + old_id + '/move'

            data = {
                'folder_id': new_id,
                '_csrf': csrf
            }

            res = requests.post(move_url, data=data, headers=headers, cookies=cookies)
            try:
                if res.status_code < 300:
                    logger.info('Move file from {} to {} successfully'.format(oldpath, newpath))
                    name = oldpath.split('/')[-1]
                    self.files.pop(oldpath)
                    self.files.update({
                        (newpath + name + ('/' if is_folder else '')): {
                            'folder': is_folder,
                            'id': old_id
                        }
                    })
                    #logger.info(self.files)
                else:
                    logger.info('Failed to move file from {} to {}'.format(oldpath, newpath))
                    logger.info('url = {}'.format(move_url))
                    logger.info('text = {}'.format(res.text))
                    logger.info('data = {}'.format(data))
                    if not(new_try):
                        logger.info('Trying to move again')
                        self.move(oldpath, newpath, new_try=True)
            except:
                logger.error('Failed to parse json when moving file from {} to {}'.format(oldpath, newpath))
                logger.info('text = {}'.format(res.text))
                if not(new_try):
                    logger.info('Trying to move again')
                    self.move(oldpath, newpath, new_try=True)

    def create_file(self, name, path):
        self.check_data()

        path += '' if len(path) == 0 or path[-1] == '/' else '/'
        if path not in self.files:
            self.create_folder(path)

        wd = self.wd
        url = wd.current_url
        if url.split('/')[-2] != 'project':
            return False
        parent_folder_id = self.files[path]['id']

        create_url = url + '/doc'
        headers, cookies, csrf = self.get_request_meta()

        data = {
            'name': name,
            'parent_folder_id': parent_folder_id,
            '_csrf': csrf
        }
        text = requests.post(create_url, data=data, headers=headers, cookies=cookies).text
        try:
            json = loads(text)
        except:
            logger.error('Failed to parse json when creating file "{}" in "{}"'.format(name, path))
            return

        if json['success']:
            self.files.update({
                path + name: {
                    'folder': True,
                    'id': json['_id']
                }
            })
            logger.info('Created file "{}" in "{}" successfully.'.format(name, path))
        else:
            logger.error('Failed to create file "{}" in "{}".'.format(name, path))
            logger.error('data = {}'.format(str(data)))
            logger.error('text = {}'.format(text))

    def delete_file(self, fullpath, new_try=False):
        self.check_data()
        if fullpath not in self.files:
            logger.error('Failed to delete file "{}". File not exists.'.format(fullpath))
            return

        headers, cookies, csrf = self.get_request_meta()
        _id = self.files[fullpath]['id']
        url = self.wd.current_url + '/doc/' + _id
        if new_try:
            url = self.wd.current_url + '/file/' + _id
        headers['X-Csrf-Token'] = csrf
        res = requests.delete(url, headers=headers, cookies=cookies)
        if res.status_code < 300:
            logger.info('Deleted file {} successfully'.format(fullpath))
            self.files.pop(fullpath)
        else:
            logger.error('Failed to delete file {}.'.format(fullpath))
            logger.error('url = {}'.format(url))
            logger.error('headers = {}'.format(str(headers)))
            logger.error('cookies = {}'.format(str(cookies)))
            logger.error('text = {}'.format(res.text))
            
            if not(new_try):
                logger.info('Trying delete again')
                self.delete_file(fullpath, new_try=True)

    def delete_folder(self, fullpath):
        self.check_data()
        fullpath += '' if len(fullpath) == 0 or fullpath[-1] == '/' else '/'
        if fullpath not in self.files:
            logger.error('Failed to delete folder "{}". File not exists.'.format(fullpath))
            return

        headers, cookies, csrf = self.get_request_meta()
        _id = self.files[fullpath]['id']
        url = self.wd.current_url + '/folder/' + _id
        headers['X-Csrf-Token'] = csrf
        if requests.delete(url, headers=headers, cookies=cookies).status_code < 300:
            logger.info('Deleted file {} successfully'.format(fullpath))
            self.files.pop(fullpath)
        else:
            logger.error('Failed to delete folder {}.'.format(fullpath))
            logger.error('text = '.format(res.text))

    def on_any_event(self, event):
        wd = self.wd
        file_abs_path = event.src_path
        file_rel_path = event.src_path.replace(getcwd() + '/', '')
        file_name = file_abs_path.split('/')[-1]

        #logger.info(event.event_type)
        #logger.info(event.src_path)
        #logger.info(event)

        #exclude hidden files

        if file_name[0] != '.':      
            if event.event_type == 'created': 
                if event.is_directory:
                    self.create_folder(file_rel_path + '/')
                else:
                # Event is created, you can process it now 
                    if exists(file_rel_path):
                        self.upload_file(file_rel_path)
                logger.info("Watchdog received created event - % s." % event.src_path) 
                #self.create_file(file_name, )

            elif event.event_type == 'modified':
                if not(event.is_directory):
                    # Event is modified, you can process it now 
                    if exists(file_rel_path):
                        self.upload_file(file_rel_path)
                    logger.info("Watchdog received modified event - % s." % event.src_path) 
            elif event.event_type == 'deleted':
                if event.is_directory:
                    self.delete_folder(file_rel_path + '/')
                else:
                    self.delete_file(file_rel_path)
                logger.info("Watchdog received deleted event - % s." % event.src_path) 
            elif event.event_type == 'moved':
                dst_rel_path = event.dest_path.replace(getcwd() + '/', '')
                dst_rel_path = '/'.join(dst_rel_path.split('/')[:-1])
                dst_rel_path += '' if len(dst_rel_path) == 0 or dst_rel_path[-1] == '/' else '/'
                self.move(file_rel_path, dst_rel_path)
                logger.info("Watchdog received moved event - from {} to {}.".format(event.src_path, event.dest_path))

if __name__ == '__main__': 
    pass