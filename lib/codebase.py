import os
import ioutil
import re

VCS_FOLDER_PAT = re.compile('\.(hg|bzr|svn|git)$')
TEST_FOLDER_PAT = re.compile('tests?$', re.IGNORECASE)
C_EXTS_PAT = re.compile('.*\.(([hc](pp|xx)?)|cc)$', re.IGNORECASE)

def is_vcs_or_test_folder(folder):
    folder = ioutil.norm_seps(folder)
    if folder.endswith('/'):
        folder = folder[0:-1]
    folder = folder.split('/')[-1]
    return bool(VCS_FOLDER_PAT.match(folder)) or bool(TEST_FOLDER_PAT.match(folder))

class Codebase:
    '''
    Make it easy to enumerate files in a particular codebase.
    '''
    def __init__(self, path, norecurse=None, novisit=None):
        if norecurse:
            norecurse = RecurseFilter(norecurse)
        else:
            norecurse = is_vcs_or_test_folder
        if novisit:
            novisit_regex = re.compile(novisit, re.IGNORECASE)
            novisit = lambda fname: bool(novisit_regex.match(fname))
        # Traverse codebase to enumerate files that need processing.
        self.root = ioutil.norm_folder(path)
        self.by_folder = {}
        self.by_ext = {}
        self._discover(norecurse, novisit)
    
    @property
    def files(self):
        for folder in self.by_folder.iterkeys():
            for item in self.by_folder[folder]:
                if not item.endswith('/'):
                    yield item
    
    def _discover(self, norecurse, novisit):
        for root, dirs, files in os.walk(self.root):
            root = ioutil.norm_folder(root)
            relative_root = root[len(self.root):]
            items = []
            for d in dirs[:]:
                if norecurse and norecurse(relative_root + d):
                    dirs.remove(d)
                else:
                    items.append(ioutil.norm_seps(relative_root + d, trailing=True))
            for f in files:
                if C_EXTS_PAT.match(f):
                    if not novisit or (not novisit(f)):
                        fname, ext = os.path.splitext(f)
                        if not ext in self.by_ext:
                            self.by_ext[ext] = []
                        self.by_ext[ext].append(relative_root + f)
                        items.append(relative_root + f)
            self.by_folder[relative_root] = items

class RecurseFilter:
    ''' Store cmdline regex to tweak how codebase is traversed.'''
    def __init__(self, regex):
        self.regex = None
        if regex:
            try:
                self.regex = re.compile(regex)
            except:
                print('Unable to compile regex "%s".' % regex)
                raise
    def __call__(self, folder):
        if codebase.is_vcs_or_test_folder(folder):
            print('skipping %s' % folder)
            return True #skip this one
        if self.regex:
            if bool(self.regex.match(folder)):
                print('skipping %s' % folder)
                return True

