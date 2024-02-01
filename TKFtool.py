from selenium import  webdriver
from selenium.webdriver.common.by import By
import random
import requests
import keyboard as kb
import time
import os
import pathlib
import json
import traceback
import atexit
import re
import math


#截图路径
ImgPath=str(pathlib.Path.home())+'\\Documents\\Escape from Tarkov\\Screenshots\\'
#位置刷新间隔（秒）
sleeptime=2
#自动截图
auto=False
#启动自动截图
on_auto='f5'
#关闭自动截图
off_auto='f6'
#截图键
key='f12'
#房间号
roomid=''
#用户id
playerid=''
#联机服务器
server=''


tmp=''

def extract_coordinates(filename):
    '''从文件名中提取坐标'''
    # 正则表达式匹配坐标
    match = re.search(r'_(\d+\.\d+), (\d+\.\d+),', filename)
    if match:
        x = float(match.group(1))
        y = float(match.group(2))
        return x, y
    return None

def calculate_angle(file1, file2):
    '''计算两个文件中坐标的角度'''
    coord1 = extract_coordinates(file1)
    coord2 = extract_coordinates(file2)

    if coord1 and coord2:
        delta_x = coord2[0] - coord1[0]
        delta_y = coord2[1] - coord1[1]
        angle_radians = math.atan2(delta_y, delta_x)
        angle_degrees = math.degrees(angle_radians)
        return angle_degrees
    return None



def getPosition():
    '''获取时间最近的截图位置信息'''
    global tmp
    # 筛选出所有 PNG 文件
    files = [f for f in os.listdir(ImgPath) if f.endswith('.png')]
    
    if not files:
        tmp = ""
        return "",None
    
    # 按修改时间降序排序
    files.sort(key=lambda x: os.path.getmtime(os.path.join(ImgPath, x)), reverse=True)
    file1,file2 = files[0], files[1]
    if file1 and file2:
        angle = calculate_angle(file1, file2)
        os.remove(ImgPath+file1)
        os.remove(ImgPath+file2)
        if angle is not None:
           return file1,angle
    return "",None


def InitDir():
    '''初始化截图文件夹'''
    dir=os.listdir(ImgPath)
    for d in dir:
        os.remove(ImgPath+d)

def setScreenShoot(event):
    '''设置自动截图状态'''
    global auto
    if event.name==on_auto:
        auto=True
    if event.name==off_auto:
        auto=False

def getConfig():
    '''获取配置文件配置'''
    global ImgPath, sleeptime, on_auto, off_auto, key, roomid, playerid, server
    if 'setting.json' not in os.listdir('.\\'):
        with open('setting.json','w') as setting:
            cfg = json.dumps({'ImgPath':ImgPath,
                            'sleeptime':sleeptime,
                            'on_auto':on_auto,
                            'off_auto':off_auto,
                            'key':key,
                            'roomid':roomid,
                            'playerid':playerid,
                            'server':server})
            setting.write(cfg)
    with open('setting.json','r') as setting:
        cfg = json.loads(setting.read())
        ImgPath=cfg['ImgPath']
        sleeptime=cfg['sleeptime']
        on_auto=cfg['on_auto']
        off_auto=cfg['off_auto']
        key=cfg['key']
        roomid=cfg['roomid']
        playerid=cfg['playerid']
        server=cfg['server']

def getMarker(driver:webdriver.Edge):
    '''获取地图标记位置'''
    marker=driver.find_element(By.XPATH, "//*[@class='marker']")
    return marker.get_attribute('style').rstrip("visibility: hidden;")+";"

# def setMarker(driver:webdriver.Edge, id, ps='', angle=None, color='#800080'):
#     '''设置新marker位置，使用SVG箭头代替原有实心圆'''
#     if not id:
#         id = 'offline'
#     try:
#         # 尝试查找是否已经有这样的marker
#         marker = driver.find_element(By.XPATH, f"//*[@id='{id}']")
#         # 如果找到，移除它，后面会创建新的
#         driver.execute_script("arguments[0].remove();", marker)
#     except:
#         # 没有找到，什么也不做，后面会创建新的
#         pass

#     # 确定箭头的旋转角度
#     transform = f"rotate({angle}deg)" if angle is not None else ""

#     # 创建SVG箭头标记
#     arrow_svg = f'''
#     <svg id='{id}' viewBox="0 0 24 24" style="{ps} {transform}">
#         <path d="M12 2L12 22M12 22L5 15M12 22L19 15" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
#     </svg>
#     '''

#     # 插入SVG箭头标记到地图中
#     js = f'''var map=document.querySelector("#map");
#              map.insertAdjacentHTML("beforeend", `{arrow_svg}`);
#           '''
#     driver.execute_script(js)


def setMarker(driver:webdriver.Edge,id,ps='',color='#f9ff01'):
    '''设置新marker位置'''
    if not id:
        id='offline'
    try:
        driver.find_element(By.XPATH, f"//*[@id='{id}']")
    except:
        js=f'''var map=document.querySelector("#map");
            map.insertAdjacentHTML("beforeend","<div id='{id}' class='marker' style='{ps}background:{color};'></div>");'''
        driver.execute_script(js)
        return
    if ps=='':
        js=f'''
        var marker=document.querySelector("#{id}");
        marker.remove();
        '''
    js=f'''var marker=document.querySelector("#{id}");
            marker.setAttribute('style','{ps}background:{color};');'''
    driver.execute_script(js)

def setPlayerData(marker)->dict:
    '''上传玩家数据到在线,返回所有玩家数据'''
    print({'player':playerid,'marker':marker})
    PlayerData=requests.post(server+roomid,json={'player':playerid,'marker':marker}).json()
    return PlayerData

"""@atexit.register
def offline():
    '''注册退出事件，退出时从服务器离线'''
    setPlayerData('')"""#无法使用

if __name__ == "__main__":
    getConfig()
    driver = webdriver.Edge()
    driver.get('https://tarkov-market.com/maps/ground-zero')
    InitDir()
    kb.on_press(setScreenShoot)#绑定键盘事件调整键盘事件
    playerList=[]
    while True:
        random_sleep_time = random.uniform(sleeptime - 0.5, sleeptime + 0.5)
        time.sleep(random_sleep_time)
        try:
            if auto: #是否自动截图
                kb.press_and_release(key)
            bt=driver.find_element(By.XPATH, "/html/body/div/div/div/div[2]/div/div/div[1]/div/input")
            bt.click()
            time.sleep(0.01)
            val,angle = getPosition()
            bt.send_keys(val)
            #新的标记渲染机制
            ps=getMarker(driver)
            marker=driver.find_element(By.XPATH,"/html/body/div/div/div/div[2]/div/div/div[4]/div")
            driver.execute_script('arguments[0].style.visibility="hidden";',marker)
            setMarker(driver,playerid,ps,color="#800080")
            #处理多人
            # if server and roomid and playerid:
            #     print("处理多人")
            #     datas=setPlayerData(getMarker(driver))
            #     for player in playerList:
            #         if player !=playerid:
            #             setMarker(driver,player)
            #     for player in datas.keys():
            #         if player != playerid:
            #             setMarker(driver,player,datas[player])
            #     playerList=datas.keys()
            #     print(setPlayerData(getMarker(driver)))
        except:
            print(traceback.format_exc())
            try:
                driver.find_element(By.XPATH, "/html/body/div/div/div/div[2]/div/div/div[1]/div/button").click()
                print('获取输入框。。。')
            except:
                print('无法打开输入框')