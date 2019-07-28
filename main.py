import os
import subprocess
import requests
from bs4 import BeautifulSoup
import datetime
initialBeginTime = 12*60
initialEndTime = 20*60
spicaAdjust = 0
slagalicaChannel = "https://www.youtube.com/user/SlagalicaRTS/videos"
logFile = "kzzlog.txt"
beginPic = "begin.bmp"
introFile = "intro25fix.mp4"
endPic = "end2.bmp"
def stamp_log():
    with open(logFile,"a") as f:
        f.write(datetime.datetime.now().ctime() + '\n')
def download_video(href):
    href = href.replace("/watch?v=","")
    command = "youtube-dl.exe https://youtu.be/"+href+" -f mp4 -o "+href+".mp4"
    p = os.system(command)
    if os.path.exists(href+".mp4"):
        with open("latestVideo.txt","w") as f:
            f.write(href)
        return href
    else:
        return False

def is_latest_video(href):
    href = href.replace("/watch?v=","")
    with open("latestVideo.txt") as f:
        localLatest = f.readline()
    return localLatest == href

def get_latest_video_info(channel):
    r = requests.get(channel)
    soup = BeautifulSoup(r.content, 'html.parser')
    return soup.select_one('.yt-lockup-title a')


def cut_video(video,begin,end,output):
    command = "ffmpeg -i "+video+" -ss "+str(begin)+" -to "+str(end)+" -c:v copy -c:a copy "+output
    altcommand = "ffmpeg -ss "+str(begin)+" -i "+video+" -t "+str(end)+" -c:v copy -c:a copy "+output
    p = os.system(command)
    
def run_command(command):
    p = subprocess.Popen(command,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    return p,iter(p.stdout.readline, b'')

def find_frame_time_command(video,frame):
    return 'ffmpeg.exe -i '+video+' -loop 1 -i '+frame+' -an -filter_complex "blend=difference:shortest=1,blackframe=99:10" -f null -'

def find_frame_time(video,frame):
    last = None
    process, processOutput = run_command(find_frame_time_command(video,frame))
    for each in processOutput:
        if "Parsed_blackframe_1" in each.decode("utf-8"):
            last = each.decode("utf-8")
            process.kill()
    time = None
    if last is not None:
        for each in last.split():
            if "t:" in each:
                time = each.replace("t:","")
    return time
def final_cut(href):
    href = href.replace("/watch?v=","")
    if not os.path.exists("initialCut"+href+".mp4"):
        cut_video(href+".mp4",initialBeginTime,initialEndTime,"initialCut"+href+".mp4")
        print("Uspeo da sasecem inicijalni")
    if os.path.exists("initialCut"+href+".mp4"):
        finalBegin = find_frame_time("initialCut"+href+".mp4",beginPic)
        print("trazim final begin i on je ",finalBegin)
        if finalBegin is not None:
            if spicaAdjust != 0:
                finalBegin = str( float(finalBegin) - spicaAdjust)
            cut_video("initialCut"+href+".mp4", float(finalBegin)+2*60, initialEndTime-initialBeginTime-5,"secondCut"+href+".mp4")
            finalEnd = find_frame_time("secondCut"+href+".mp4",endPic)
            if finalEnd is not None:
                cut_video(href+".mp4",initialBeginTime+float(finalBegin),initialBeginTime+float(finalBegin)+2*60+float(finalEnd),"final"+href+".mp4")
    else:
        print("Ne posotji inicijalni cut")
def clean_up(href):
    href = href.replace("/watch?v=","")
    if os.path.exists("initialCut"+href+".mp4"):
        os.system("del initialCut"+href+".mp4")
    if os.path.exists("secondCut"+href+".mp4"):
        os.system("del secondCut"+href+".mp4")
    if os.path.exists(href+".mp4"):
        os.system("del "+href+".mp4")
    if ((not os.path.exists("initialCut"+href+".mp4")) and (not os.path.exists("secondCut"+href+".mp4")) and (not os.path.exists(href+".mp4"))):
        print("Cleanup complete")
    else:
        print("Couldn't clean up")
def main():
    ytLatest = get_latest_video_info(slagalicaChannel)
    if not is_latest_video(ytLatest["href"]):
        check = download_video(ytLatest["href"])
        if check:
            if not os.path.exists("final"+ytLatest["href"].replace("/watch?v=","")+".mp4"):
                final_cut(ytLatest["href"])
                if os.path.exists("final"+ytLatest["href"].replace("/watch?v=","")+".mp4"):
                    stamp_log()
                    add_intro(ytLatest["href"])
                    print("Success")
                    clean_up(ytLatest["href"])
                    #post_to_facebook(ytLatest)
            else:
                print("File already exists " + ytLatest["href"].replace("/watch?v=",""))
                if not os.path.exists("introfinal"+ytLatest["href"].replace("/watch?v=","")+".mp4"):
                        add_intro(ytLatest["href"])
                        print("added intro")

        else:
            print("Failure to download the video")
    else:
        print("Already have the latest video")
def add_intro(href):
    href = href.replace("/watch?v=","")
    command = "(echo file '" + introFile + "' & echo file 'final"+href+".mp4' )>list.txt"
    command2 = "ffmpeg -fflags +igndts -safe 0 -f concat -i list.txt -c copy introfinal"+href+".mp4"
    command2alt = "ffmpeg -safe 0 -f concat -segment_time_metadata 1 -i list.txt -vf select=concatdec_select -af aselect=concatdec_select,aresample=async=1 introfinal"+href+".mp4"
    p = os.system(command)
    p = os.system(command2alt)

def post_to_facebook(ytLatest):
    from selenium import webdriver
    from time import sleep
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.keys import Keys
    import os
    from credentials import login
    usr = login['username']
    pwd = login['password']
    linkToModal = login['linkToModal']
    videoPath = login['videoPath']
    speed = 5
    if usr:
        options = Options()
        #options.add_argument("--headless")
        #options.add_argument('window-size=1920x1080');
        driver = webdriver.Chrome(executable_path = './chromedriver.exe', options = options)
        #<--- code to login --->
        driver.get('https://en-gb.facebook.com/login')
        usr_box = driver.find_element_by_id('email')
        usr_box.send_keys(usr)
        pwd_box = driver.find_element_by_id('pass')
        pwd_box.send_keys(pwd)
        login_button = driver.find_element_by_id('loginbutton')
        login_button.submit()
        sleep(speed)
        print("logged in")
        driver.get(linkToModal)
        sleep(speed)
        print("Uploading")
        give = driver.find_element_by_xpath("//input[@type='file']")
        href = ytLatest
        give.send_keys(videoPath+"introfinal"+ytLatest["href"].replace("/watch?v=","")+".mp4")
        #Wait for wall
        sleep(speed)
        naslov = ytLatest['title']
        description = "https://www.youtube.com"+ytLatest['href']
        title = driver.find_element_by_xpath("//input[@placeholder='Add a title for your video here...']")
        title.send_keys(naslov)
        title.send_keys(Keys.TAB, Keys.TAB, description)

        sleep(speed)
        btn = driver.find_element_by_xpath("//*[@data-testid='VIDEO_COMPOSER_NEXT_BUTTON']")
        btn.click()
        sleep(speed*3)
        btn2 = driver.find_element_by_xpath("//*[@data-testid='VIDEO_COMPOSER_PUBLISH_BUTTON']")
        btn2.click()
        print("finished")
        sleep(speed*3)
        driver.close()
    return True    
main()



    
