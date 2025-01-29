import requests
import os
import re
from datetime import datetime
from win32com.client import Dispatch
PATH = r"E:\VKbot_down"

def create_shortcut(target_path, shortcut_path):
    '''Creates a shortcut '''
    index = 1
    new_path = shortcut_path
    while True:
        # print(os.listdir(current_path))
        if not os.path.exists(new_path):
            shortcut_path = new_path
            break
        new_path = shortcut_path[:-4] + f"_{index}" + shortcut_path[-4:]
        index+=1

    shortcut = Dispatch("WScript.Shell").CreateShortcut(shortcut_path)
    shortcut.TargetPath = target_path
    shortcut.WorkingDirectory = os.path.dirname(target_path)
    shortcut.save()

def path_creator(path):
    now = datetime.now()
    date = now.strftime(r"%Y\%b\%d")
    current_path = rf'{path}\{date}'

    os.makedirs(current_path, exist_ok=True)
    file_name = now.strftime(r"%H-%M")
    index = 0
    while True:
        # print(os.listdir(current_path))
        if not any(re.match(rf"{file_name}{f'_{str(index)}'.replace('_0', '')}\..+", file) for file in
                   os.listdir(current_path)):
            # if the file is the first one remove index
            return rf"{current_path}\{file_name}{f'_{str(index)}'.replace('_0', '')}"
        index += 1


def down_smart(url, ext='jpg'):
    extensions = {'jpg': 'images',
                  'png': 'images',
                  'txt': 'files',
                  'doc': 'files',
                  'pdf': 'files',
                  'mp4': 'video',
                  'mkv': 'video',
                  'mp3': 'audio',
                  'wav': 'audio'}
    try:
        response = requests.get(url, stream=True)
        total_len_mb = int(response.headers.get('Content-Length')) / (1024 * 1024)

        file_name = path_creator(rf"{PATH}\main\{extensions.get(ext, 'none_of_this')}")
        # print(file_name)

        with open(f"{file_name}.{ext}", 'wb') as file:
            counter = 0
            for chunk in response.iter_content(chunk_size=1024*1024*3):
                print(f"downloaded {round((counter/total_len_mb)*100, 2)} %")
                counter += 3
                if chunk:
                    file.write(chunk)
            # file.write(response.content)
        print("Downloaded successfully")

        if total_len_mb > 30:
            print("Shortcut created")
            create_shortcut(f"{file_name}.{ext}", rf"{PATH}\heavy\{extensions.get(ext, 'none_of_this')}\shortcut_{round(total_len_mb)}MB.lnk")
            # os.symlink(file_name, rf"{PATH}\heavy\{extensions.get(ext, 'none_of_this')}")
    except Exception as exp:
        print("Something went wrong...")
        # return exp
        raise exp


if __name__ == '__main__':
    # down_smart('https://assets.mmsrg.com/isr/166325/c1/-/ASSET_MMS_141874716?x=536&y=402&format=jpg&quality=80&sp=yes&strip=yes&trim&ex=536&ey=402&align=center&resizesource&unsharp=1.5x1+0.7+0.02&cox=0&coy=0&cdx=536&cdy=402')
    down_smart('https://www.myinstants.com/media/sounds/emotional-damage-meme.mp3', ext='mp3')
    # down_smart('https://videos.pexels.com/video-files/1409899/1409899-uhd_2560_1440_25fps.mp4', ext='mp4')
    # down_smart('https://www.shutterstock.com/shutterstock/videos/1038882452/preview/stock-footage-a-thunderstorm-raging-in-the-distance-off-the-coast-of-mooloolaba-sunshine-coast-australia.webm', ext='mp4')
    # down_smart('https://videos.pexels.com/video-files/1893746/1893746-uhd_2560_1440_25fps.mp4', ext='mp4')
    # print("%Y\%b\%d")
