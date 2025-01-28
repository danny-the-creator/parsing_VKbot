import requests
import os
import re
from datetime import datetime

PATH = r"E:\VKbot_down\main\none_of_this"

def path_creator():
    now = datetime.now()
    date = now.strftime(r"%Y\%b\%d")
    current_path =rf'{PATH}\{date}'

    os.makedirs(current_path, exist_ok=True)
    file_name = now.strftime(r"%H-%M")
    index = 0
    while True:
        print(os.listdir(current_path))
        if not any(re.match(rf"{file_name}{f'_{str(index)}'.replace('_0', '')}\....", file) for file in os.listdir(current_path)):
            # if the file is the first one remove index
            return rf"{current_path}\{file_name}{f'_{str(index)}'.replace('_0', '')}"
        index += 1

def down_image(url, ext= 'jpg'):
    try:
        response = requests.get(url)
        file_name = path_creator()
        print(file_name)
        with open(f"{file_name}.{ext}", 'wb') as file:
            file.write(response.content)
        print("Downloaded successfully")
    except Exception as exp:
        print("Something went wrong...")
        return exp

if __name__ == '__main__':
    down_image('https://assets.mmsrg.com/isr/166325/c1/-/ASSET_MMS_141874716?x=536&y=402&format=jpg&quality=80&sp=yes&strip=yes&trim&ex=536&ey=402&align=center&resizesource&unsharp=1.5x1+0.7+0.02&cox=0&coy=0&cdx=536&cdy=402')
    # print(path_creator())

    # print("%Y\%b\%d")