"""This module has DownloadManager class which is used to download files from the internet.

Example
-------
>>> from downloader import DownloadManager
>>> manager = DownloadManager()
>>> manager.download('https://www.example.com/example.jpg', 'example.jpg')

>>> from downloader import DownloadManager
>>> manager = DownloadManager()
>>> manager.download('https://www.example.com/example.jpg', 'example.jpg', 8)

>>> from downloader import DownloadManager
>>> manager = DownloadManager("/home/user/Downloads")
>>> manager.download('https://www.example.com/example.jpg', 'example.jpg')

>>> from downloader import DownloadManager
>>> manager = DownloadManager(verbose=False)
>>> manager.download('https://www.example.com/example.jpg', 'example.jpg')


"""
import typer
import requests
import threading
import os
import time
import atpbar


class DownloadManager:
    """This class is used to download files from the internet."""
    def __init__(self, destination: str = None, verbose: bool = True):
        """This method is used to initialize the class.

        Parameters
        ----------
        destination : str
            The destination of the downloaded files.

        """
        if destination is None:
            self.destination = os.getcwd()
        else:
            self.destination = destination

        if not verbose:
            atpbar.disable()

    def handler(self, start: int, end: int, url: str, filename: str = None, name: str = "") -> None:
        """This method is used to download a file from the internet.

        Parameters
        ----------
        start : int
            The starting position of the file.
        end : int
            The ending position of the file.
        url : str
            The URL of the file.
        filename : str
            The name of the file.
        name : str
            The name of the thread.

        """
        filename = os.path.join(self.destination, filename)
        headers = {'Range': f'bytes={start}-{end}'}
        res = requests.get(url, headers=headers, stream=True)
        dl = 0
        total_length = int(res.headers.get('content-length'))
        with open(filename, "r+b") as fp:
            st = time.time()
            fp.seek(start)
            content_iter = res.iter_content(chunk_size=1024)
            for _ in atpbar.atpbar(range(0, total_length, 1024), name=name):
                chunk = next(content_iter)
                dl += len(chunk)
                fp.write(chunk)

    def download(self, url: str, name: str = None, number_of_threads: int = 4) -> None:
        """This method is used to download a file from the internet.

        Parameters
        ----------
        url : str
            The URL of the file.
        name : str
            The name of the file.
        number_of_threads : int
            The number of threads to use.

        """
        res = requests.head(url)
        if name:
            file_name = name
        else:
            file_name = url.split('/')[-1]
        try:
            file_size = int(res.headers['content-length'])
        except Exception as e:
            typer.secho(str(e), fg=typer.colors.RED)
            print("Invalid URL")
            return

        part = int(file_size) // number_of_threads
        file_name = os.path.join(self.destination, file_name)
        fp = open(file_name, "wb")
        fp.write(b'\0' * file_size)
        fp.close()

        for i in range(number_of_threads):
            start = part * i
            if i == number_of_threads - 1:
                end = file_size
            else:
                end = start + part

            t = threading.Thread(target=self.handler,
                                 kwargs={'start': start, 'end': end, 'url': url,
                                         'filename': file_name, 'name': f"thead no. {i}"})
            t.daemon = True
            t.start()

        main_thread = threading.current_thread()
        for t in threading.enumerate():
            if t is main_thread:
                continue
            t.join()
        atpbar.flush()