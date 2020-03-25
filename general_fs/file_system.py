import os



class FileSystem():
    def listdir(self, parent, **kwargs):
        raise NotImplementedError

    def join(self, path, *paths):
        return os.path.join(path, *paths)

    def read_txt(self, path):
        raise NotImplementedError

    def write_txt(self, path, txt, append=False):
        raise NotImplementedError

    def isdir(self, path):
        raise NotImplementedError

    def isfile(self, path):
        raise NotImplementedError

    def mkdir(self, path, **kwargs):
        raise NotImplementedError

    def glob(self, pattern):
        raise NotImplementedError

    def splitext(self, path):
        return os.path.splitext(path)

    def basename(self, path):
        return os.path.basename(path)

    def exists(self, path):
        raise NotImplementedError

    def delete(self, path):
        raise NotImplementedError



