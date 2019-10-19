import os
import subprocess
import requests
from bs4 import BeautifulSoup
import datetime
initialBeginTime = 11*60
initialEndTime = 20*60
spicaAdjust = 0
fullRun = True
#fullRun = False
slagalicaChannel = "https://www.youtube.com/user/SlagalicaRTS/videos"
logFile = "kzzlog.txt"
beginPic = "begin.bmp"
introFile = "intro25fix.mp4"
endPic = "end2.bmp"
logAll = True
checkForLatestVideo = True
def resize_frame(frame,w,h):
    from PIL import Image
    image = Image.open(frame)
    newImage = image.resize((w,h),Image.ANTIALIAS)
    newImage.save("begin"+str(h)+".bmp")

    
def get_video_resolution(href):
    command = 'ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 '+href+".mp4"
    log(command)
    process, processOutput = run_command(command)
    #counter = 0
    #reso = ''.split()
    #while (len(reso) < 2 or counter < 3):
    #    reso = next(processOutput).decode("utf-8").strip().split(',')
    #    counter+=1
    reso = next(processOutput).decode("utf-8").strip().split(',')
    dim = dict()
    log("(get_video_resolution) "+str(dim))
    dim['w'] = reso[0]
    dim['h'] = reso[1]
    return dim


def stamp_log():
#    with open(logFile,"a") as f:
#        f.write(datetime.datetime.now().ctime() + '\n')
    return '[' +str(datetime.datetime.now().ctime()) + '] '
def log(msg):
    msg = stamp_log() + str(msg)
    print(msg)
    if logAll:
        with open(logFile,"a") as f:
            f.write(str(msg) + '\n')
def download_video(href):
    log("Trying to download video")
    href = href.replace("/watch?v=","")
    href = href.replace("VIDEO","")
    command = "youtube-dl.exe https://youtu.be/"+href+" -f mp4 -o VIDEO"+href+".mp4"
    log(command)
    p = os.system(command)
    if os.path.exists("VIDEO"+href+".mp4"):
        with open("latestVideo.txt","w") as f:
            f.write(href)
        return href
    else:
        return False

def is_latest_video(href):
    href = href.replace("/watch?v=","")
    with open("latestVideo.txt") as f:
        localLatest = f.readline()
    return (localLatest == href) and checkForLatestVideo

def get_latest_video_info(channel):
    r = requests.get(channel)
    soup = BeautifulSoup(r.content, 'html.parser')
    yt = soup.select_one('.yt-lockup-title a')
    yt['href'] = "VIDEO"+yt['href']
    return yt


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
    log('ffmpeg.exe -i '+video+' -loop 1 -i '+frame+' -an -filter_complex "blend=difference:shortest=1,blackframe=99:10" -f null -')
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
    dim = get_video_resolution(href)
    log(dim)
    if not os.path.exists("begin"+str(dim['h'])+".bmp"):
        log("FOUND NEW RESOULTION")
        resize_frame("begin.bmp",dim['w'],dim['h'])
        beginPic = "begin"+str(dim['h'])+".bmp"
        resize_frame("end.bmp",dim['w'],dim['h'])
        endPic = "end"+str(dim['h'])+".bmp"
    else:
        beginPic = "begin"+str(dim['h'])+".bmp"
        endPic = "end"+str(dim['h'])+".bmp"
    if not os.path.exists("initialCut"+href+".mp4"):
        cut_video(href+".mp4",initialBeginTime,initialEndTime,"initialCut"+href+".mp4")
        log("Uspeo da sasecem inicijalni")
    else:
        log("Inicijalni vec postoji")
    if os.path.exists("initialCut"+href+".mp4"):
        finalBegin = find_frame_time("initialCut"+href+".mp4",beginPic)
        log("trazim final begin i on je "+str(finalBegin))
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
    if os.path.exists("final"+href+".mp4"):
        os.system("move secondCut"+href+".mp4 Earlier/")
    if os.path.exists("introfinal"+href+".mp4"):
        os.system("del introfinal"+href+".mp4")
    if ((not os.path.exists("initialCut"+href+".mp4")) and (not os.path.exists("secondCut"+href+".mp4")) and (not os.path.exists(href+".mp4"))):
        log("Cleanup complete")
    else:
        log("Couldn't clean up")
def main():
    ytLatest = get_latest_video_info(slagalicaChannel)
    if not is_latest_video(ytLatest["href"]):
        check = download_video(ytLatest["href"])
        if check:
            if not os.path.exists("final"+ytLatest["href"].replace("/watch?v=","")+".mp4"):
                final_cut(ytLatest["href"])
                if os.path.exists("final"+ytLatest["href"].replace("/watch?v=","")+".mp4"):
                    #stamp_log()
                    add_intro(ytLatest["href"])
                    log("Success")
                    log("Posting to facebook")
                    post_to_facebook(ytLatest)
                    #clean_up(ytLatest["href"])
            else:
                log("File already exists " + str(ytLatest["href"].replace("/watch?v=","")))
                if not os.path.exists("introfinal"+ytLatest["href"].replace("/watch?v=","")+".mp4"):
                        add_intro(ytLatest["href"])
                        log("added intro")

        else:
            log("Failure to download the video")
    else:
        log("Already have the latest video")
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
    ytLatest['href'] = ytLatest['href'].replace("/watch?v=","")
    print(ytLatest['href'])
    if not os.path.exists("introfinal"+ytLatest['href']+".mp4"):
        log("Ne postoji video")
        return
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
        log("logged in")
        driver.get(linkToModal)
        sleep(speed)
        log("Uploading")
        give = driver.find_element_by_xpath("//input[@data-testid='media-attachment-add-photo']")
        href = ytLatest
        log("give.send_keys(" + videoPath+"introfinal"+ytLatest["href"].replace("/watch?v=","")+".mp4")
        give.send_keys(videoPath+"introfinal"+ytLatest["href"].replace("/watch?v=","")+".mp4")
        #Wait for wall
        sleep(speed*5)
        naslov = ytLatest['title']
        description = naslov + " https://www.youtube.com"+ytLatest['href'].replace("VIDEO","")
        title = driver.find_element_by_xpath("//input[@placeholder='Add a title for your video here...']")
        title.send_keys(naslov)
        title.send_keys(Keys.TAB,Keys.TAB, description)

        sleep(speed)
        btn = driver.find_element_by_xpath("//*[@data-testid='VIDEO_COMPOSER_NEXT_BUTTON']")
        btn.click()
        sleep(speed*3)
        btn2 = driver.find_element_by_xpath("//*[@data-testid='VIDEO_COMPOSER_PUBLISH_BUTTON']")
        btn2.click()
        log("finished")
        sleep(speed*3)
        driver.close()
    return True    
if fullRun:
    main()
else:
    p = post_to_facebook
    l = get_latest_video_info(slagalicaChannel)



    
