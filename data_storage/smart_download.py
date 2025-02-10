import requests
import os
import re
from datetime import datetime
from win32com.client import Dispatch
from itertools import takewhile
from bs4 import BeautifulSoup
PATH = r"E:\VKbot_down"

def create_shortcut(target_path, shortcut_path):
    """Creates a shortcut"""
    index = 1
    new_path = shortcut_path

    while True:
        # if there is a shortcut with the same name, increase the index
        if not os.path.exists(new_path):
            shortcut_path = new_path
            break
        new_path = shortcut_path[:-4] + f"_{index}" + shortcut_path[-4:]
        index+=1

    # needed to create shortcuts on Windows
    shortcut = Dispatch("WScript.Shell").CreateShortcut(shortcut_path)
    shortcut.TargetPath = target_path
    shortcut.WorkingDirectory = os.path.dirname(target_path)
    shortcut.save()


def imp_path(imp, dir=''):
    name = 'link'       # default name
    path = re.sub(r"[,. /\\]", r" ", imp).strip().split()

    new_path = list(takewhile(lambda elem: "?" not in elem, path))  # takes all the element till '?'
    if len(new_path) != len(path):
        new_path.append(path[len(new_path)])
    path = new_path         # probably will need to move this part in another function

    # print(new_path)
    if "?" in path[-1]:     # denotes the name of the link
        if '?' == path[-1]:
            path[-2] = path[-2]+path[-1]
            path = path[:-1]

        name = path[-1].replace('?', '')
        path = path[:-1]

    path = ("/".join(path))
    os.makedirs(f"{dir}/{path}", exist_ok=True)
    return f"{dir}/{path}/{name}.lnk"


def path_creator(path):
    """Creates a path based on current date and returns it with the name of the file which is current time"""
    now = datetime.now()
    date = now.strftime(r"%Y\%b\%d")
    file_name = now.strftime(r"%H-%M")

    current_path = rf'{path}\{date}'
    os.makedirs(current_path, exist_ok=True)

    index = 0
    while True:
        if not any(re.match(rf"{file_name}{('_'+str(index)).replace('_0', '')}\..+", file) for file in
                   os.listdir(current_path)):
            # if the file is the first one remove index
            return rf"{current_path}\{file_name}{f'_{str(index)}'.replace('_0', '')}"
        index += 1

def convert_url(resp):
    """Converts url to the indirect website into the url to direct file (which is located on this website)"""
    soup = BeautifulSoup(resp.content, "lxml")
    new_url = soup.find("a", class_='FlatButton FlatButton--primary FlatButton--size-l').get('href')
    return new_url

def down_smart(url, ext='jpg', imp=None):
    extensions = {'jpg': 'images',
                  'png': 'images',
                  'txt': 'files',
                  'docx': 'files',
                  'pdf': 'files',
                  'mp4': 'video',
                  'mkv': 'video',
                  'mp3': 'audio',
                  'wav': 'audio'}

    try:
        response = requests.get(url, stream=True)

        if 'text/html;' in response.headers.get('Content-Type') and ext != 'html':
            # if we get html file, but expect something else, we need to find the right link in this html file
            response = requests.get(convert_url(response), stream=True)                  # to do this we use convert_url

        total_len = response.headers.get('Content-Length')
        total_len_mb = int(total_len) / (1024 * 1024) if total_len else 10
        file_name = path_creator(rf"{PATH}\main\{extensions.get(ext, 'none_of_this')}")
        # print(file_name)

        # Saving the file here (in chunks)
        with open(f"{file_name}.{ext}", 'wb') as file:
            counter = 0
            for chunk in response.iter_content(chunk_size=1024*1024*3):
                if chunk:
                    file.write(chunk)

                print(f"downloaded {round((counter/total_len_mb)*100, 2)} %")
                counter += 3
        print("Downloaded successfully")

        if imp is not None:
            create_shortcut(f"{file_name}.{ext}", imp_path(imp, dir=rf"{PATH}\important\{extensions.get(ext, 'none_of_this')}"))
            print("important shortcut created")
        elif total_len_mb > 30:
            create_shortcut(f"{file_name}.{ext}", rf"{PATH}\heavy\{extensions.get(ext, 'none_of_this')}\shortcut_{round(total_len_mb)}MB.lnk")
            print("heavy shortcut created")
    except Exception as exp:
        print("Something went wrong...")
        # raise exp
        print(exp)


if __name__ == '__main__':
    # down_smart('https://www.shutterstock.com/shutterstock/videos/1038882452/preview/stock-footage-a-thunderstorm-raging-in-the-distance-off-the-coast-of-mooloolaba-sunshine-coast-australia.webm', ext='mp4')
    down_smart('https://videos.pexels.com/video-files/1893746/1893746-uhd_2560_1440_25fps.mp4', ext='mp4')
    down_smart('https://videos.pexels.com/video-files/1893746/1893746-uhd_2560_1440_25fps.mp4', ext='mp4', imp='  test  , first')
    # print(imp_path('    work ai , beta, geta   .    done        /   /   /  geto    \\  prin  new_survey     ?      bghjkl yyujj 778  '))
    down_smart('https://www.myinstants.com/media/sounds/emotional-damage-meme.mp3', ext='mp3', imp='// work    ai   ,  new_survey  ?   ')