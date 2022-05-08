from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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
import random

# adding path to geckodriver to the OS environment variable
# assuming that it is stored at the same path as this script
os.environ["PATH"] += os.pathsep + os.getcwd()
download_path = "dataset/"

def main():
    # Adapted from a solution by Piees and atif93 on stackoverflow
    # https://stackoverflow.com/questions/20716842/python-download-images-from-google-image-search
    searchtext = sys.argv[1] # the search query
    num_requested = int(sys.argv[2]) # number of images to download
    number_of_scrolls = int(num_requested / 200 + 1) 
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
        # does not work:
        #try:
        #    WebDriverWait(driver, 1000000).until(EC.element_to_be_clickable((By.XPATH, "//input[@value='Show more results']"))).click()
        #except Exception as e:
        #    print ("Less images found:", e)
        #    break

    # imges = driver.find_elements_by_xpath('//div[@class="rg_meta"]') # not working anymore
    # imges = driver.find_elements_by_xpath('//div[contains(@class,"rg_meta")]')
    imges = driver.find_elements_by_css_selector("img.Q4LuWd")
    print ("Total images:", len(imges), "\n")
    print ("Downloading...")
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
        # this seems to be the stopping point for amnt of actual images
        if downloaded_img_count >= 250:
            break

    print ("Total downloaded: ", downloaded_img_count, "/", img_count)

    resize_images(searchtext);

    make_clip(searchtext, num_requested);
    
    driver.quit()

def resize_images(name):
    print ("Converting images...")
    time.sleep(2)
    for file in glob.glob("dataset\\" + name.replace(" ", "_") + "\\*.jpg"):
        i = Image.open(file);
        i = i.resize((250, 200))
        i = i.convert('RGB')
        i.save(file)
        

def make_clip(name, numberOfImages):
    clips = []
    
    images = len(glob.glob("dataset\\" + name.replace(" ", "_") + "\\*.jpg"))
    vidLen = 24

    first = ColorClip((250, 200), (50, 150, 255), duration=20)
    text = TextClip("top " + str(numberOfImages) + " " + name, fontsize=30, color='white')
    text = text.set_pos('center').set_duration(20)
    first = CompositeVideoClip([first, text])
    clips.append(first)
    
    for x in range(numberOfImages):
        txtOne = ColorClip((250, 200), (50, 150, 255), duration=2.5)
        txtTwo = TextClip("number " + str(numberOfImages - x), fontsize=30, color='white')
        txtTwo = txtTwo.set_pos('center').set_duration(2.5)
        txtTwo = CompositeVideoClip([txtOne, txtTwo])
        clips.append(txtTwo)
        vidLen = vidLen + 2.5

        numImage = str(x)
        if (numberOfImages >= images):
            numImage = str(random.randint(0, images - 1))
        
        img = ImageClip("dataset\\" + name.replace(" ", "_") + "\\" + str(numImage) + ".jpg").set_duration(3).set_position("center")
        clip = ColorClip((250, 200), (50, 150, 255), duration=3)
        clip = CompositeVideoClip([clip, img])
        clips.append(clip)
        vidLen = vidLen + 3
    
    endOne = ColorClip((250, 200), (50, 150, 255), duration=4)
    endTwo = TextClip("thx for whatcing", fontsize=30, color='white')
    endTwo = endTwo.set_pos('center').set_duration(4)
    endTwo = CompositeVideoClip([endOne, endTwo])
    clips.append(endTwo)

    first = concatenate_videoclips(clips)

    audio = make_audio(name, vidLen)
    first.audio = audio

    first.write_videofile(name + '.mp4', fps=30)

    #bitrate = vidLen / 6

    #ffmpeg -i ../../tos.avi -c:v libx264 -b:v 500k tos_500k.mp4
    # reduce bitrate
    subprocess.call(['ffmpeg', '-i', name + '.mp4', '-b:a', '12k', '-b:v', '6k', name + '2.mp4'])
    # name + '.mp4', '-b:a', '15k', '-vcodec', 'libx265', '-crf', '30', name + '2.mp4'

    # cut first 15 sec because the bitrate is very biased to the beginning for some reason. it is ugly
    # so i made the beginning very long so we could cut it here
    subprocess.call(['ffmpeg', '-i', name + '2.mp4', '-ss', '15', name + '3.mp4'])

def make_audio(name, vidLength):
    original = AudioClip(lambda t: [ 0 ])
    original = original.set_duration(15)
    nextClips = [original]
    totalTime = 0

    while (totalTime < vidLength):
        print(str(totalTime) + " " + str(vidLength))
        for file in glob.glob("music\\" + name.replace(" ", "_") + "\\*.mp3"):
            audioclip = AudioFileClip(file)
            nextClips.append(audioclip)
            totalTime = totalTime + audioclip.duration

    print(str(totalTime) + " " + str(vidLength))
    original = concatenate_audioclips(nextClips)
    original = original.set_end(vidLength)
    return original

if __name__ == "__main__":
    main()
