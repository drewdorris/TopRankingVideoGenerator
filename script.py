from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from moviepy.editor import *
from PIL import Image
import os
import subprocess
import json
import urllib.request
import urllib.error
import sys
import time
import glob

# adding path to geckodriver to the OS environment variable
# assuming that it is stored at the same path as this script
os.environ["PATH"] += os.pathsep + os.getcwd()
download_path = "dataset/"

def main():
    searchtext = sys.argv[1] # the search query
    num_requested = int(sys.argv[2]) # number of images to download
    number_of_scrolls = int(num_requested / 400 + 1) 
    # number_of_scrolls * 400 images will be opened in the browser

    if not os.path.exists(download_path + searchtext.replace(" ", "_")):
        os.makedirs(download_path + searchtext.replace(" ", "_"))

    url = "https://www.google.com/search?q="+searchtext+"&source=lnms&tbm=isch"
    driver = webdriver.Firefox()
    driver.get(url)

    headers = {}
    headers['User-Agent'] = "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36"
    extensions = {"jpg", "jpeg", "png", "gif"}
    img_count = 0
    downloaded_img_count = 0

    for _ in range(number_of_scrolls):
        for __ in range(10):
            # multiple scrolls needed to show all 400 images
            driver.execute_script("window.scrollBy(0, 1000000)")
            time.sleep(0.2)
        # to load next 400 images
        time.sleep(0.5)

    # imges = driver.find_elements_by_xpath('//div[@class="rg_meta"]') # not working anymore
    # imges = driver.find_elements_by_xpath('//div[contains(@class,"rg_meta")]')
    imges = driver.find_elements_by_css_selector("img.Q4LuWd")
    print ("Total images:", len(imges), "\n")
    for img in imges:
        img_count += 1
        img_url = img.get_attribute('src')
        img_type = "jpg"
        #print ("Downloading image", img_count, ": ", img_url)
        try:
            if img_type not in extensions:
                img_type = "jpg"
            req = urllib.request.Request(img_url, headers=headers)
            raw_img = urllib.request.urlopen(req).read()
            f = open(download_path+searchtext.replace(" ", "_")+"/"+str(downloaded_img_count)+"."+img_type, "wb")
            f.write(raw_img)
            f.close
            downloaded_img_count += 1
        except Exception as e:
            print ("Download failed:", e)
        finally:
            print
        if downloaded_img_count >= num_requested:
            break

    print ("Total downloaded: ", downloaded_img_count, "/", img_count)

    resize_images(searchtext);

    make_clip(searchtext);
    
    driver.quit()

def resize_images(name):
    for file in glob.glob("dataset\\" + name.replace(" ", "_") + "\\*.jpg"):
        print("aaa")
        i = Image.open(file);
        i = i.resize((400, 300))
        i = i.convert('RGB')
        i.save(file)
        

def make_clip(name):
    images = len(glob.glob("dataset\\" + name.replace(" ", "_") + "\\*.jpg"))
    vidLen = 24

    first = ColorClip((400, 300), (50, 150, 255), duration=20)
    text = TextClip("top " + str(images) + " " + name, fontsize=40, color='white')
    text = text.set_pos('center').set_duration(20)
    first = CompositeVideoClip([first, text])
    
    for x in range(images):
        txtOne = ColorClip((400, 300), (50, 150, 255), duration=3)
        txtTwo = TextClip("number " + str(images - x), fontsize=40, color='white')
        txtTwo = txtTwo.set_pos('center').set_duration(3)
        txtTwo = CompositeVideoClip([txtOne, txtTwo])
        first = concatenate_videoclips([first, txtTwo])
        vidLen = vidLen + 3
        
        img = (ImageClip("dataset\\" + name.replace(" ", "_") + "\\" + str(x) + ".jpg").set_duration(4).set_position(("center", "center")))
        clip = ColorClip((400, 300), (50, 150, 255), duration=4)
        clip = CompositeVideoClip([clip, img])
        first = concatenate_videoclips([first, clip])
        vidLen = vidLen + 4
    
    endOne = ColorClip((400, 300), (50, 150, 255), duration=4)
    endTwo = TextClip("thx for whatcing", fontsize=40, color='white')
    endTwo = endTwo.set_pos('center').set_duration(4)
    endTwo = CompositeVideoClip([endOne, endTwo])
    first = concatenate_videoclips([first, endTwo])

    first.write_videofile(name + '.mp4', fps=30)

    #bitrate = vidLen / 6

    #ffmpeg -i ../../tos.avi -c:v libx264 -b:v 500k tos_500k.mp4
    # reduce bitrate
    subprocess.call(['ffmpeg', '-i', name + '.mp4', '-b:v', '10k', name + '2.mp4'])

    # cut first 15 sec because the bitrate is very biased to the beginning for some reason. it is ugly
    # so i made the beginning very long so we could cut it here
    subprocess.call(['ffmpeg', '-i', name + '2.mp4', '-ss', '15', name + '3.mp4'])

if __name__ == "__main__":
    main()
