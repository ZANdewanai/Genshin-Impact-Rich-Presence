import copy
import os
import sys
import time

sys.path.append(os.path.abspath(os.path.join('python', 'packages')))
sys.path.append(os.path.abspath(os.path.join('python')))
import psutil
import psutil._exceptions as ps_exceptions
from discoIPC import ipc

## this is where the path to the log(Player.log) is, AKA where the rich presence reads whats happening and converts it to something it can use
## yours should be in the same folder of this

def main():
    Player_log_path = "Player.log".format(os.getenv('UserProfile'))


## rich presence stuff

    start_time = int(time.time())
    activity = {'details': 'In Game',  # this is what gets modified and sent to Discord via discordIPC
                'timestamps': {'start': start_time},
                'assets': {'small_image': ' ', 'small_text': 'Genshin Impact', 'large_image': 'logo', 'large_text': 'Genshin Impact'},
                'state': 'Not Tracking'}
    client_connected = False
    has_mention_not_running = False

    while True:
        game_is_running = False
        discord_is_running = False
        next_delay = 5

        for process in psutil.process_iter():
            if game_is_running and discord_is_running:
                break
            else:
                try:
                    with process.oneshot():
                        p_name = process.name()

                        if p_name == 'GenshinImpact.exe':
                            start_time = int(process.create_time())
                            activity['timestamps']['start'] = start_time
                            game_is_running = True
                        elif 'Discord' in p_name:
                            discord_is_running = True
                except ps_exceptions.NoSuchProcess:
                    pass
                except ps_exceptions.AccessDenied:
                    pass

                time.sleep(0.001)

        if game_is_running and discord_is_running:
            if not client_connected:
                # connects to Discord
                client = ipc.DiscordIPC('944346292568596500')
                client.connect()
                client_connected = True

            with open(Player_log_path, 'r', errors='replace') as Player_log:
                Player = Player_log.readlines()

            old_details_state = copy.copy((activity['details'], activity['state'], activity['assets']['small_image'], activity['assets']['small_text']))
            
## end of rich presence stuff

            for line in Player:  
            
## this is for the player character     

                    if 'Zan¢' in line:  # here you put your name ( example =   if 'YourNameHere¢' in line:  )
                        activity['assets']['small_image'] = 'aether' # if you are playing as female/male MC change to lumine/aether  ( example = activity['assets']['small_image'] = 'lumine')
                        activity['assets']['small_text'] = 'Playing as Zan' # here you change your name display  ( example =  activity['assets']['small_text'] = 'Playing as YourNameHere' )     

                    if 'Zan 4' in line: # here you put your name ( example =   if 'YourNameHere 4' in line:  )
                        activity['assets']['small_image'] = 'aether' # if you are playing as female/male MC change to lumine/aether  ( example = activity['assets']['small_image'] = 'lumine')
                        activity['assets']['small_text'] = 'Playing as Zan' # here you change your name display  ( example =  activity['assets']['small_text'] = 'Playing as YourNameHere' )   

                    if 'Zan«' in line: # here you put your name ( example =   if 'YourNameHere«' in line:  )
                        activity['assets']['small_image'] = 'aether' # if you are playing as female/male MC change to lumine/aether  ( example = activity['assets']['small_image'] = 'lumine')
                        activity['assets']['small_text'] = 'Playing as Zan' # here you change your name display  ( example =  activity['assets']['small_text'] = 'Playing as YourNameHere' )    

                    if 'Zan#' in line: # here you put your name ( example =   if 'YourNameHere#' in line:  )
                        activity['assets']['small_image'] = 'aether' # if you are playing as female MC change to    activity['assets']['small_image'] = 'lumine'
                        activity['assets']['small_text'] = 'Playing as Zan' # here you change your name display  ( example =  activity['assets']['small_text'] = 'Playing as YourNameHere' )  

## this is for every other character    

    # Mondstadt Characters
 
                    if 'Venti«' in line:
                        activity['assets']['small_image'] = 'venti'
                        activity['assets']['small_text'] = 'Playing as Venti'
               
                    if 'Venti¢' in line:
                        activity['assets']['small_image'] = 'venti'
                        activity['assets']['small_text'] = 'Playing as Venti'
                        
                    if 'Venti#' in line:
                        activity['assets']['small_image'] = 'venti'
                        activity['assets']['small_text'] = 'Playing as Venti'
                        
                    if 'Venti 4' in line:
                        activity['assets']['small_image'] = 'venti'
                        activity['assets']['small_text'] = 'Playing as Venti'

#--------------------------------------------------------------------------------------

                    if 'Jean¢' in line:
                        activity['assets']['small_image'] = 'jean'
                        activity['assets']['small_text'] = 'Playing as Jean'
               
                    if 'Jean#' in line:
                        activity['assets']['small_image'] = 'jean'
                        activity['assets']['small_text'] = 'Playing as Jean'
                        
                    if 'Jean«' in line:
                        activity['assets']['small_image'] = 'jean'
                        activity['assets']['small_text'] = 'Playing as Jean' 
                                        
                    if 'Jean 4' in line:
                        activity['assets']['small_image'] = 'jean'
                        activity['assets']['small_text'] = 'Playing as Jean' 

#--------------------------------------------------------------------------------------

                    if 'Razor#' in line:
                        activity['assets']['small_image'] = 'razor'
                        activity['assets']['small_text'] = 'Playing as Razor'
                        
                    if 'Razor 4' in line:
                        activity['assets']['small_image'] = 'razor'
                        activity['assets']['small_text'] = 'Playing as Razor'
                        
                    if 'Razor«' in line:
                        activity['assets']['small_image'] = 'razor'
                        activity['assets']['small_text'] = 'Playing as Razor' 
                                        
                    if 'Razor¢' in line:
                        activity['assets']['small_image'] = 'razor'
                        activity['assets']['small_text'] = 'Playing as Razor' 

#--------------------------------------------------------------------------------------
         
                    if 'Lisa#' in line:
                        activity['assets']['small_image'] = 'lisa'
                        activity['assets']['small_text'] = 'Playing as Lisa'
               
                    if 'Lisa 4' in line:
                        activity['assets']['small_image'] = 'lisa'
                        activity['assets']['small_text'] = 'Playing as Lisa'
                        
                    if 'Lisa«' in line:
                        activity['assets']['small_image'] = 'lisa'
                        activity['assets']['small_text'] = 'Playing as Lisa' 
                                        
                    if 'Lisa¢' in line:
                        activity['assets']['small_image'] = 'lisa'
                        activity['assets']['small_text'] = 'Playing as Lisa' 
                        
#--------------------------------------------------------------------------------------

                    if 'Diluc¢' in line:
                        activity['assets']['small_image'] = 'diluc'
                        activity['assets']['small_text'] = 'Playing as Diluc'
               
                    if 'Diluc«' in line:
                        activity['assets']['small_image'] = 'diluc'
                        activity['assets']['small_text'] = 'Playing as Diluc'
                        
                    if 'Diluc 4' in line:
                        activity['assets']['small_image'] = 'diluc'
                        activity['assets']['small_text'] = 'Playing as Diluc'
                                       
                    if 'Diluc#' in line:
                        activity['assets']['small_image'] = 'diluc'
                        activity['assets']['small_text'] = 'Playing as Diluc'

#--------------------------------------------------------------------------------------
        
                    if 'Sucrose¢' in line:
                        activity['assets']['small_image'] = 'sucrose'
                        activity['assets']['small_text'] = 'Playing as Sucrose'
               
                    if 'Sucrose«' in line:
                        activity['assets']['small_image'] = 'sucrose'
                        activity['assets']['small_text'] = 'Playing as Sucrose'
                                       
                    if 'Sucrose 4' in line:
                        activity['assets']['small_image'] = 'sucrose'
                        activity['assets']['small_text'] = 'Playing as Sucrose'
                                                               
                    if 'Sucrose4' in line:
                        activity['assets']['small_image'] = 'sucrose'
                        activity['assets']['small_text'] = 'Playing as Sucrose'
                        
                    if 'Sucrose#' in line:
                        activity['assets']['small_image'] = 'sucrose'
                        activity['assets']['small_text'] = 'Playing as Sucrose'
                     
#--------------------------------------------------------------------------------------  
        
                    if 'Amber#' in line:
                        activity['assets']['small_image'] = 'amber'
                        activity['assets']['small_text'] = 'Playing as Amber'
               
                    if 'Amber«' in line:
                        activity['assets']['small_image'] = 'amber'
                        activity['assets']['small_text'] = 'Playing as Amber'
               
                    if 'Amber¢' in line:
                        activity['assets']['small_image'] = 'amber'
                        activity['assets']['small_text'] = 'Playing as Amber'
                                       
                    if 'Amber 4' in line:
                        activity['assets']['small_image'] = 'amber'
                        activity['assets']['small_text'] = 'Playing as Amber'
                        
#--------------------------------------------------------------------------------------      
                  
                    if 'Barbara#' in line:
                        activity['assets']['small_image'] = 'barbara'
                        activity['assets']['small_text'] = 'Playing as Barbara'
               
                    if 'Barbara«' in line:
                        activity['assets']['small_image'] = 'barbara'
                        activity['assets']['small_text'] = 'Playing as Barbara'
               
                    if 'Barbara¢' in line:
                        activity['assets']['small_image'] = 'barbara'
                        activity['assets']['small_text'] = 'Playing as Barbara'
                                       
                    if 'Barbara 4' in line:
                        activity['assets']['small_image'] = 'barbara'
                        activity['assets']['small_text'] = 'Playing as Barbara'
                        
#--------------------------------------------------------------------------------------      
                  
                    if 'Bennett#' in line:
                        activity['assets']['small_image'] = 'bennet'
                        activity['assets']['small_text'] = 'Playing as Bennett'
               
                    if 'Bennett«' in line:
                        activity['assets']['small_image'] = 'bennet'
                        activity['assets']['small_text'] = 'Playing as Bennett'
               
                    if 'Bennett¢' in line:
                        activity['assets']['small_image'] = 'bennet'
                        activity['assets']['small_text'] = 'Playing as Bennett'
                                       
                    if 'Bennett 4' in line:
                        activity['assets']['small_image'] = 'bennet'
                        activity['assets']['small_text'] = 'Playing as Bennett'
                        
#--------------------------------------------------------------------------------------      
                  
                    if 'Diona#' in line:
                        activity['assets']['small_image'] = 'diona'
                        activity['assets']['small_text'] = 'Playing as Diona'
               
                    if 'Diona«' in line:
                        activity['assets']['small_image'] = 'diona'
                        activity['assets']['small_text'] = 'Playing as Diona'
               
                    if 'Diona¢' in line:
                        activity['assets']['small_image'] = 'diona'
                        activity['assets']['small_text'] = 'Playing as Diona'
                                       
                    if 'Diona 4' in line:
                        activity['assets']['small_image'] = 'diona'
                        activity['assets']['small_text'] = 'Playing as Diona'
                        
#--------------------------------------------------------------------------------------      
                          
                    if 'Eula#' in line:
                        activity['assets']['small_image'] = 'eula'
                        activity['assets']['small_text'] = 'Playing as Eula'
               
                    if 'Eula«' in line:
                        activity['assets']['small_image'] = 'eula'
                        activity['assets']['small_text'] = 'Playing as Eula'
               
                    if 'Eula¢' in line:
                        activity['assets']['small_image'] = 'eula'
                        activity['assets']['small_text'] = 'Playing as Eula'
                                       
                    if 'Eula 4' in line:
                        activity['assets']['small_image'] = 'eula'
                        activity['assets']['small_text'] = 'Playing as Eula'
                        
#--------------------------------------------------------------------------------------      
                                  
                    if 'Fischl#' in line:
                        activity['assets']['small_image'] = 'fischl'
                        activity['assets']['small_text'] = 'Playing as Fischl'
               
                    if 'Fischl«' in line:
                        activity['assets']['small_image'] = 'fischl'
                        activity['assets']['small_text'] = 'Playing as Fischl'
               
                    if 'Fischl¢' in line:
                        activity['assets']['small_image'] = 'fischl'
                        activity['assets']['small_text'] = 'Playing as Fischl'
                                       
                    if 'Fischl 4' in line:
                        activity['assets']['small_image'] = 'fischl'
                        activity['assets']['small_text'] = 'Playing as Fischl'
                        
#--------------------------------------------------------------------------------------      
                                          
                    if 'Kaeya#' in line:
                        activity['assets']['small_image'] = 'kaeya'
                        activity['assets']['small_text'] = 'Playing as Kaeya'
               
                    if 'Kaeya«' in line:
                        activity['assets']['small_image'] = 'kaeya'
                        activity['assets']['small_text'] = 'Playing as Kaeya'
               
                    if 'Kaeya¢' in line:
                        activity['assets']['small_image'] = 'kaeya'
                        activity['assets']['small_text'] = 'Playing as Kaeya'
                                       
                    if 'Kaeya 4' in line:
                        activity['assets']['small_image'] = 'kaeya'
                        activity['assets']['small_text'] = 'Playing as Kaeya'
                        
#--------------------------------------------------------------------------------------      
                                          
                    if 'Klee#' in line:
                        activity['assets']['small_image'] = 'klee'
                        activity['assets']['small_text'] = 'Playing as Klee'
               
                    if 'Klee«' in line:
                        activity['assets']['small_image'] = 'klee'
                        activity['assets']['small_text'] = 'Playing as Klee'
               
                    if 'Klee¢' in line:
                        activity['assets']['small_image'] = 'klee'
                        activity['assets']['small_text'] = 'Playing as Klee'
                                       
                    if 'Klee 4' in line:
                        activity['assets']['small_image'] = 'klee'
                        activity['assets']['small_text'] = 'Playing as Klee'
                        
#--------------------------------------------------------------------------------------      
                                          
                    if 'Mona#' in line:
                        activity['assets']['small_image'] = 'mona'
                        activity['assets']['small_text'] = 'Playing as Mona'
               
                    if 'Mona«' in line:
                        activity['assets']['small_image'] = 'mona'
                        activity['assets']['small_text'] = 'Playing as Mona'
               
                    if 'Mona¢' in line:
                        activity['assets']['small_image'] = 'mona'
                        activity['assets']['small_text'] = 'Playing as Mona'
                                       
                    if 'Mona 4' in line:
                        activity['assets']['small_image'] = 'mona'
                        activity['assets']['small_text'] = 'Playing as Mona'
                        
#--------------------------------------------------------------------------------------      
                                                  
                    if 'Noelle#' in line:
                        activity['assets']['small_image'] = 'noelle'
                        activity['assets']['small_text'] = 'Playing as Noelle'
               
                    if 'Noelle«' in line:
                        activity['assets']['small_image'] = 'noelle'
                        activity['assets']['small_text'] = 'Playing as Noelle'
               
                    if 'Noelle¢' in line:
                        activity['assets']['small_image'] = 'noelle'
                        activity['assets']['small_text'] = 'Playing as Noelle'
                                       
                    if 'Noelle 4' in line:
                        activity['assets']['small_image'] = 'noelle'
                        activity['assets']['small_text'] = 'Playing as Noelle'
                        
#--------------------------------------------------------------------------------------      
                                                  
                    if 'Rosaria#' in line:
                        activity['assets']['small_image'] = 'rosaria'
                        activity['assets']['small_text'] = 'Playing as Rosaria'
               
                    if 'Rosaria«' in line:
                        activity['assets']['small_image'] = 'rosaria'
                        activity['assets']['small_text'] = 'Playing as Rosaria'
               
                    if 'Rosaria¢' in line:
                        activity['assets']['small_image'] = 'rosaria'
                        activity['assets']['small_text'] = 'Playing as Rosaria'
                                       
                    if 'Rosaria 4' in line:
                        activity['assets']['small_image'] = 'rosaria'
                        activity['assets']['small_text'] = 'Playing as Rosaria'
                        
#--------------------------------------------------------------------------------------      
        
    # Liyue Characters
    
                    if 'Xiao«' in line:
                        activity['assets']['small_image'] = 'xiao'
                        activity['assets']['small_text'] = 'Playing as Xiao'
                          
                    if 'Xiao<' in line:
                        activity['assets']['small_image'] = 'xiao'
                        activity['assets']['small_text'] = 'Playing as Xiao'
                                                   
                    if 'Xiao¢' in line:
                        activity['assets']['small_image'] = 'xiao'
                        activity['assets']['small_text'] = 'Playing as Xiao'
                                                   
                    if 'Xiao#' in line:
                        activity['assets']['small_image'] = 'xiao'
                        activity['assets']['small_text'] = 'Playing as Xiao'  
                        
                    if 'Xiao 4' in line:
                        activity['assets']['small_image'] = 'xiao'
                        activity['assets']['small_text'] = 'Playing as Xiao'    

#--------------------------------------------------------------------------------------
        
                    if 'Ningguang#' in line:
                        activity['assets']['small_image'] = 'ningguang'
                        activity['assets']['small_text'] = 'Playing as Ningguang'
                        
                    if 'Ningguang¢' in line:
                        activity['assets']['small_image'] = 'ningguang'
                        activity['assets']['small_text'] = 'Playing as Ningguang'
                         
                    if 'Ningguang 4' in line:
                        activity['assets']['small_image'] = 'ningguang'
                        activity['assets']['small_text'] = 'Playing as Ningguang'
                           
                    if 'Ningguang«' in line:
                        activity['assets']['small_image'] = 'ningguang'
                        activity['assets']['small_text'] = 'Playing as Ningguang'
  
#--------------------------------------------------------------------------------------    
                    if 'Beidou¢' in line:
                        activity['assets']['small_image'] = 'beidou'
                        activity['assets']['small_text'] = 'Playing as Beidou'
               
                    if 'Beidou«' in line:
                        activity['assets']['small_image'] = 'beidou'
                        activity['assets']['small_text'] = 'Playing as Beidou'
                                      
                    if 'Beidou 4' in line:
                        activity['assets']['small_image'] = 'beidou'
                        activity['assets']['small_text'] = 'Playing as Beidou'

                    if 'Beidou4' in line:
                        activity['assets']['small_image'] = 'beidou'
                        activity['assets']['small_text'] = 'Playing as Beidou'

#--------------------------------------------------------------------------------------
           
                    if 'Zhongli#' in line:
                        activity['assets']['small_image'] = 'zhongli'
                        activity['assets']['small_text'] = 'Playing as Zhongli'
                                                            
                    if 'Zhongli¢' in line:
                        activity['assets']['small_image'] = 'zhongli'
                        activity['assets']['small_text'] = 'Playing as Zhongli'
                                                                                
                    if 'Zhongli ye' in line:
                        activity['assets']['small_image'] = 'zhongli'
                        activity['assets']['small_text'] = 'Playing as Zhongli'
                        
                    if 'Zhongli 4' in line:
                        activity['assets']['small_image'] = 'zhongli'
                        activity['assets']['small_text'] = 'Playing as Zhongli'
                                                
                    if 'Zhongli«' in line:
                        activity['assets']['small_image'] = 'zhongli'
                        activity['assets']['small_text'] = 'Playing as Zhongli'
                        
#-------------------------------------------------------------------------------------- 

                    if 'Ganyu¢' in line:
                        activity['assets']['small_image'] = 'ganyu'
                        activity['assets']['small_text'] = 'Playing as Ganyu'
                                        
                    if 'Ganyu#' in line:
                        activity['assets']['small_image'] = 'ganyu'
                        activity['assets']['small_text'] = 'Playing as Ganyu'
                                                            
                    if 'Ganyu 4' in line:
                        activity['assets']['small_image'] = 'ganyu'
                        activity['assets']['small_text'] = 'Playing as Ganyu'
                                                        
                    if 'Ganyu«' in line:
                        activity['assets']['small_image'] = 'ganyu'
                        activity['assets']['small_text'] = 'Playing as Ganyu'

#-------------------------------------------------------------------------------------- 

                    if 'Xiangling#' in line:
                        activity['assets']['small_image'] = 'xiangling'
                        activity['assets']['small_text'] = 'Playing as Xiangling'
               
                    if 'Xiangling¢' in line:
                        activity['assets']['small_image'] = 'xiangling'
                        activity['assets']['small_text'] = 'Playing as Xiangling'
                                   
                    if 'Xiangling?' in line:
                        activity['assets']['small_image'] = 'xiangling'
                        activity['assets']['small_text'] = 'Playing as Xiangling'
                                       
                    if 'Xiangling 4' in line:
                        activity['assets']['small_image'] = 'xiangling'
                        activity['assets']['small_text'] = 'Playing as Xiangling'

#--------------------------------------------------------------------------------------
         
                    if 'Xinyan#' in line:
                        activity['assets']['small_image'] = 'xinyan'
                        activity['assets']['small_text'] = 'Playing as Xinyan'
               
                    if 'Xinyan 4' in line:
                        activity['assets']['small_image'] = 'xinyan'
                        activity['assets']['small_text'] = 'Playing as Xinyan'
                        
                    if 'Xinyan«' in line:
                        activity['assets']['small_image'] = 'xinyan'
                        activity['assets']['small_text'] = 'Playing as Xinyan' 
                                        
                    if 'Xinyan¢' in line:
                        activity['assets']['small_image'] = 'xinyan'
                        activity['assets']['small_text'] = 'Playing as Xinyan' 
#--------------------------------------------------------------------------------------
         
                    if 'Xingqiu#' in line:
                        activity['assets']['small_image'] = 'xingqiu'
                        activity['assets']['small_text'] = 'Playing as Xingqiu'
               
                    if 'Xingqiu 4' in line:
                        activity['assets']['small_image'] = 'xingqiu'
                        activity['assets']['small_text'] = 'Playing as Xingqiu'
                        
                    if 'Xingqiu«' in line:
                        activity['assets']['small_image'] = 'xingqiu'
                        activity['assets']['small_text'] = 'Playing as Xingqiu' 
                                        
                    if 'Xingqiu¢' in line:
                        activity['assets']['small_image'] = 'xingqiu'
                        activity['assets']['small_text'] = 'Playing as Xingqiu' 

#--------------------------------------------------------------------------------------
          
                    if 'Hu Tao¢' in line:
                        activity['assets']['small_image'] = 'hu_tao'
                        activity['assets']['small_text'] = 'Playing as Hu Tao'
               
                    if 'Hu Tao«' in line:
                        activity['assets']['small_image'] = 'hu_tao'
                        activity['assets']['small_text'] = 'Playing as Hu Tao'
                                      
                    if 'Hu Tao 4' in line:
                        activity['assets']['small_image'] = 'hu_tao'
                        activity['assets']['small_text'] = 'Playing as Hu Tao'
                                                       
                    if 'Hu Tao#' in line:
                        activity['assets']['small_image'] = 'hu_tao'
                        activity['assets']['small_text'] = 'Playing as Hu Tao'
                 
#--------------------------------------------------------------------------------------
          
                    if 'Chongyun#' in line:
                        activity['assets']['small_image'] = 'chongyun'
                        activity['assets']['small_text'] = 'Playing as Chongyun'
               
                    if 'Chongyun«' in line:
                        activity['assets']['small_image'] = 'chongyun'
                        activity['assets']['small_text'] = 'Playing as Chongyun'
               
                    if 'Chongyun¢' in line:
                        activity['assets']['small_image'] = 'chongyun'
                        activity['assets']['small_text'] = 'Playing as Chongyun'
                                       
                    if 'Chongyun 4' in line:
                        activity['assets']['small_image'] = 'chongyun'
                        activity['assets']['small_text'] = 'Playing as Chongyun'
                        
#--------------------------------------------------------------------------------------
          
                    if 'Shenhe#' in line:
                        activity['assets']['small_image'] = 'shenhe'
                        activity['assets']['small_text'] = 'Playing as Shenhe'
               
                    if 'Shenhe«' in line:
                        activity['assets']['small_image'] = 'shenhe'
                        activity['assets']['small_text'] = 'Playing as Shenhe'
               
                    if 'Shenhe¢' in line:
                        activity['assets']['small_image'] = 'shenhe'
                        activity['assets']['small_text'] = 'Playing as Shenhe'
                                       
                    if 'Shenhe 4' in line:
                        activity['assets']['small_image'] = 'shenhe'
                        activity['assets']['small_text'] = 'Playing as Shenhe'
                        
#--------------------------------------------------------------------------------------      
          
                    if 'Keqing#' in line:
                        activity['assets']['small_image'] = 'keqing'
                        activity['assets']['small_text'] = 'Playing as Keqing'
               
                    if 'Keqing«' in line:
                        activity['assets']['small_image'] = 'keqing'
                        activity['assets']['small_text'] = 'Playing as Keqing'
               
                    if 'Keqing¢' in line:
                        activity['assets']['small_image'] = 'keqing'
                        activity['assets']['small_text'] = 'Playing as Keqing'
                                       
                    if 'Keqing 4' in line:
                        activity['assets']['small_image'] = 'keqing'
                        activity['assets']['small_text'] = 'Playing as Keqing'
                        
#--------------------------------------------------------------------------------------   
          
                    if 'Qiqi#' in line:
                        activity['assets']['small_image'] = 'qiqi'
                        activity['assets']['small_text'] = 'Playing as Qiqi'
               
                    if 'Qiqi«' in line:
                        activity['assets']['small_image'] = 'qiqi'
                        activity['assets']['small_text'] = 'Playing as Qiqi'
               
                    if 'Qiqi¢' in line:
                        activity['assets']['small_image'] = 'qiqi'
                        activity['assets']['small_text'] = 'Playing as Qiqi'
                                       
                    if 'Qiqi 4' in line:
                        activity['assets']['small_image'] = 'qiqi'
                        activity['assets']['small_text'] = 'Playing as Qiqi'
                        
#--------------------------------------------------------------------------------------
          
                    if 'Jin#' in line:
                        activity['assets']['small_image'] = 'yun_jin'
                        activity['assets']['small_text'] = 'Playing as Yun Jin'
               
                    if 'Jin«' in line:
                        activity['assets']['small_image'] = 'yun_jin'
                        activity['assets']['small_text'] = 'Playing as Yun Jin'
               
                    if 'Jin¢' in line:
                        activity['assets']['small_image'] = 'yun_jin'
                        activity['assets']['small_text'] = 'Playing as Yun Jin'
                                       
                    if 'Jin 4' in line:
                        activity['assets']['small_image'] = 'yun_jin'
                        activity['assets']['small_text'] = 'Playing as Yun Jin'
                        
#--------------------------------------------------------------------------------------   
          
                    if 'Yanfei#' in line:
                        activity['assets']['small_image'] = 'yanfei'
                        activity['assets']['small_text'] = 'Playing as Yanfei'
               
                    if 'Yanfei«' in line:
                        activity['assets']['small_image'] = 'yanfei'
                        activity['assets']['small_text'] = 'Playing as Yanfei'
               
                    if 'Yanfei¢' in line:
                        activity['assets']['small_image'] = 'yanfei'
                        activity['assets']['small_text'] = 'Playing as Yanfei'
                                       
                    if 'Yanfei 4' in line:
                        activity['assets']['small_image'] = 'yanfei'
                        activity['assets']['small_text'] = 'Playing as Yanfei'
                        
#--------------------------------------------------------------------------------------   

    # Inazuma Characters

                    if 'Kazuha¢' in line:
                        activity['assets']['small_image'] = 'kaedehara_kazuha'
                        activity['assets']['small_text'] = 'Playing as Kaedehara Kazuha'
                        
                    if 'Kazuha *' in line:
                        activity['assets']['small_image'] = 'kaedehara_kazuha'
                        activity['assets']['small_text'] = 'Playing as Kaedehara Kazuha'
                                                                                   
                    if 'Kazuha #' in line:
                        activity['assets']['small_image'] = 'kaedehara_kazuha'
                        activity['assets']['small_text'] = 'Playing as Kaedehara Kazuha'
                                                                                                           
                    if 'Kazuha 4' in line:
                        activity['assets']['small_image'] = 'kaedehara_kazuha'
                        activity['assets']['small_text'] = 'Playing as Kaedehara Kazuha'

#--------------------------------------------------------------------------------------

                    if 'Yae Miko#' in line:
                        activity['assets']['small_image'] = 'yae_miko'
                        activity['assets']['small_text'] = 'Playing as Yae Miko'
               
                    if 'Yae Miko«' in line:
                        activity['assets']['small_image'] = 'yae_miko'
                        activity['assets']['small_text'] = 'Playing as Yae Miko'
               
                    if 'Yae Miko¢' in line:
                        activity['assets']['small_image'] = 'yae_miko'
                        activity['assets']['small_text'] = 'Playing as Yae Miko'
                                       
                    if 'Yae Miko 4' in line:
                        activity['assets']['small_image'] = 'yae_miko'
                        activity['assets']['small_text'] = 'Playing as Yae Miko'
                        
#--------------------------------------------------------------------------------------
   
                    if 'Shogun#' in line:
                        activity['assets']['small_image'] = 'raiden_shogun'
                        activity['assets']['small_text'] = 'Playing as Raiden Shogun'
               
                    if 'Shogun«' in line:
                        activity['assets']['small_image'] = 'raiden_shogun'
                        activity['assets']['small_text'] = 'Playing as Raiden Shogun'
               
                    if 'Shogun¢' in line:
                        activity['assets']['small_image'] = 'raiden_shogun'
                        activity['assets']['small_text'] = 'Playing as Raiden Shogun'
                                       
                    if 'Shogun 4' in line:
                        activity['assets']['small_image'] = 'raiden_shogun'
                        activity['assets']['small_text'] = 'Playing as Raiden Shogun'
                        
#--------------------------------------------------------------------------------------         

                    if 'Yoimiya#' in line:
                        activity['assets']['small_image'] = 'yoimiya'
                        activity['assets']['small_text'] = 'Playing as Yoimiya'
               
                    if 'Yoimiya«' in line:
                        activity['assets']['small_image'] = 'yoimiya'
                        activity['assets']['small_text'] = 'Playing as Yoimiya'
               
                    if 'Yoimiya¢' in line:
                        activity['assets']['small_image'] = 'yoimiya'
                        activity['assets']['small_text'] = 'Playing as Yoimiya'
                                       
                    if 'Yoimiya 4' in line:
                        activity['assets']['small_image'] = 'yoimiya'
                        activity['assets']['small_text'] = 'Playing as Yoimiya'
                        
#--------------------------------------------------------------------------------------  
 
                    if 'Thoma#' in line:
                        activity['assets']['small_image'] = 'thoma'
                        activity['assets']['small_text'] = 'Playing as Thoma'
               
                    if 'Thoma«' in line:
                        activity['assets']['small_image'] = 'thoma'
                        activity['assets']['small_text'] = 'Playing as Thoma'
               
                    if 'Thoma¢' in line:
                        activity['assets']['small_image'] = 'thoma'
                        activity['assets']['small_text'] = 'Playing as Thoma'
                                       
                    if 'Thoma 4' in line:
                        activity['assets']['small_image'] = 'thoma'
                        activity['assets']['small_text'] = 'Playing as Thoma'
                        
#--------------------------------------------------------------------------------------        
          
                    if 'Sayu#' in line:
                        activity['assets']['small_image'] = 'sayu'
                        activity['assets']['small_text'] = 'Playing as Sayu'
               
                    if 'Sayu«' in line:
                        activity['assets']['small_image'] = 'sayu'
                        activity['assets']['small_text'] = 'Playing as Sayu'
               
                    if 'Sayu¢' in line:
                        activity['assets']['small_image'] = 'sayu'
                        activity['assets']['small_text'] = 'Playing as Sayu'
                                       
                    if 'Sayu 4' in line:
                        activity['assets']['small_image'] = 'sayu'
                        activity['assets']['small_text'] = 'Playing as Sayu'
                        
#--------------------------------------------------------------------------------------        
          
                    if 'Kokomi#' in line:
                        activity['assets']['small_image'] = 'sangonomiya_kokomi'
                        activity['assets']['small_text'] = 'Playing as Sangonomiya Kokomi'
               
                    if 'Kokomi«' in line:
                        activity['assets']['small_image'] = 'sangonomiya_kokomi'
                        activity['assets']['small_text'] = 'Playing as Sangonomiya Kokomi'
               
                    if 'Kokomi¢' in line:
                        activity['assets']['small_image'] = 'sangonomiya_kokomi'
                        activity['assets']['small_text'] = 'Playing as Sangonomiya Kokomi'
                                       
                    if 'Kokomi 4' in line:
                        activity['assets']['small_image'] = 'sangonomiya_kokomi'
                        activity['assets']['small_text'] = 'Playing as Sangonomiya Kokomi'
                        
#--------------------------------------------------------------------------------------           
                   
                    if 'Itto#' in line:
                        activity['assets']['small_image'] = 'arataki_itto'
                        activity['assets']['small_text'] = 'Playing as Arataki Itto'
               
                    if 'Itto«' in line:
                        activity['assets']['small_image'] = 'arataki_itto'
                        activity['assets']['small_text'] = 'Playing as Arataki Itto'
               
                    if 'Itto¢' in line:
                        activity['assets']['small_image'] = 'arataki_itto'
                        activity['assets']['small_text'] = 'Playing as Arataki Itto'
                                       
                    if 'Itto 4' in line:
                        activity['assets']['small_image'] = 'arataki_itto'
                        activity['assets']['small_text'] = 'Playing as Arataki Itto'
                        
#--------------------------------------------------------------------------------------        
                                      
                    if 'Sara#' in line:
                        activity['assets']['small_image'] = 'kujo_sara'
                        activity['assets']['small_text'] = 'Playing as Kujou Sara'
               
                    if 'Sara«' in line:
                        activity['assets']['small_image'] = 'kujo_sara'
                        activity['assets']['small_text'] = 'Playing as Kujou Sara'
               
                    if 'Sara¢' in line:
                        activity['assets']['small_image'] = 'kujo_sara'
                        activity['assets']['small_text'] = 'Playing as Kujou Sara'
                                       
                    if 'Sara 4' in line:
                        activity['assets']['small_image'] = 'kujo_sara'
                        activity['assets']['small_text'] = 'Playing as Kujou Sara'
                        
#--------------------------------------------------------------------------------------        
                   
                    if 'Gorou#' in line:
                        activity['assets']['small_image'] = 'gorou'
                        activity['assets']['small_text'] = 'Playing as Gorou'
               
                    if 'Gorou«' in line:
                        activity['assets']['small_image'] = 'gorou'
                        activity['assets']['small_text'] = 'Playing as Gorou'
               
                    if 'Gorou¢' in line:
                        activity['assets']['small_image'] = 'gorou'
                        activity['assets']['small_text'] = 'Playing as Gorou'
                                       
                    if 'Gorou 4' in line:
                        activity['assets']['small_image'] = 'gorou'
                        activity['assets']['small_text'] = 'Playing as Gorou'
                        
#--------------------------------------------------------------------------------------        
                   
                    if 'Ayaka#' in line:
                        activity['assets']['small_image'] = 'kamisato_ayaka'
                        activity['assets']['small_text'] = 'Playing as Kamisato Ayaka'
               
                    if 'Ayaka«' in line:
                        activity['assets']['small_image'] = 'kamisato_ayaka'
                        activity['assets']['small_text'] = 'Playing as Kamisato Ayaka'
               
                    if 'Ayaka¢' in line:
                        activity['assets']['small_image'] = 'kamisato_ayaka'
                        activity['assets']['small_text'] = 'Playing as Kamisato Ayaka'
                                       
                    if 'Ayaka 4' in line:
                        activity['assets']['small_image'] = 'kamisato_ayaka'
                        activity['assets']['small_text'] = 'Playing as Kamisato Ayaka'
                        
#--------------------------------------------------------------------------------------        
                            
                    if 'Ayato#' in line:
                        activity['assets']['small_image'] = 'kamisato_ayato'
                        activity['assets']['small_text'] = 'Playing as Kamisato Ayato'
               
                    if 'Ayato«' in line:
                        activity['assets']['small_image'] = 'kamisato_ayato'
                        activity['assets']['small_text'] = 'Playing as Kamisato Ayato'
               
                    if 'Ayato¢' in line:
                        activity['assets']['small_image'] = 'kamisato_ayato'
                        activity['assets']['small_text'] = 'Playing as Kamisato Ayato'
                                       
                    if 'Ayato 4' in line:
                        activity['assets']['small_image'] = 'kamisato_ayato'
                        activity['assets']['small_text'] = 'Playing as Kamisato Ayato'
                        
#--------------------------------------------------------------------------------------        
         
    # Snezhnaya Characters
      
                            
                    if 'Tartaglia#' in line:
                        activity['assets']['small_image'] = 'tartaglia'
                        activity['assets']['small_text'] = 'Playing as Tartaglia'
               
                    if 'Tartaglia«' in line:
                        activity['assets']['small_image'] = 'tartaglia'
                        activity['assets']['small_text'] = 'Playing as Tartaglia'
               
                    if 'Tartaglia¢' in line:
                        activity['assets']['small_image'] = 'tartaglia'
                        activity['assets']['small_text'] = 'Playing as Tartaglia'
                                       
                    if 'Tartaglia 4' in line:
                        activity['assets']['small_image'] = 'tartaglia'
                        activity['assets']['small_text'] = 'Playing as Tartaglia'
                        
#--------------------------------------------------------------------------------------        
         
    # Collab Characters
      
                            
                    if 'Aloy#' in line:
                        activity['assets']['small_image'] = 'aloy'
                        activity['assets']['small_text'] = 'Playing as Aloy'
               
                    if 'Aloy«' in line:
                        activity['assets']['small_image'] = 'aloy'
                        activity['assets']['small_text'] = 'Playing as Aloy'
               
                    if 'Aloy¢' in line:
                        activity['assets']['small_image'] = 'aloy'
                        activity['assets']['small_text'] = 'Playing as Aloy'
                                       
                    if 'Aloy 4' in line:
                        activity['assets']['small_image'] = 'aloy'
                        activity['assets']['small_text'] = 'Playing as Aloy'
                      
#--------------------------------------------------------------------------------------

## this is for the place you are on

    # Mondstadt
     
    #Starfell Valley
    
                    if 'Mondstadt' in line:
                        activity['details'] = "Traveling In Mondstadt"
                        activity['state'] = "Mondstadt - Starfell Valley"
                        activity = switch_image_mode(activity, ('mondstadt', 'Traveling In Mondstadt'))
                        
                    if 'Cider Lake' in line:
                        activity['details'] = "Traveling In Mondstadt"
                        activity['state'] = "Cider Lake - Starfell Valley"
                        activity = switch_image_mode(activity, ('mondstadt', 'Traveling In Mondstadt'))

                    if 'Whispering Woods' in line:
                        activity['details'] = "Traveling In Mondstadt"
                        activity['state'] = "Whispering Woods - Starfell Valley"
                        activity = switch_image_mode(activity, ('whisperingwoods', 'Traveling In Mondstadt'))
                        
                    if 'fell Lake' in line:
                        activity['details'] = "Traveling In Mondstadt"
                        activity['state'] = "Starfell Lake - Starfell Valley"
                        activity = switch_image_mode(activity, ('starfelllake', 'Traveling In Mondstadt'))
                        
                    if 'snatch Cliff' in line:
                        activity['details'] = "Traveling In Mondstadt"
                        activity['state'] = "Starsnatch Cliff - Starfell Valley"
                        activity = switch_image_mode(activity, ('starsnatchcliff', 'Traveling In Mondstadt'))
                        
                    if 'bearer Mountains' in line:
                        activity['details'] = "Traveling In Mondstadt"
                        activity['state'] = "Stormbearer Mountains - Starfell Valley"
                        activity = switch_image_mode(activity, ('stormbearermountains', 'Traveling In Mondstadt'))
                        
                    if 'Point' in line:
                        activity['details'] = "Traveling In Mondstadt"
                        activity['state'] = "Stormbearer Point - Starfell Valley"
                        activity = switch_image_mode(activity, ('stormbearerpoint', 'Traveling In Mondstadt'))
                        
                    if 'Thousand' in line:
                        activity['details'] = "Traveling In Mondstadt"
                        activity['state'] = "Thousand Winds Temple - Starfell Valley"
                        activity = switch_image_mode(activity, ('thousandwindstemple', 'Traveling In Mondstadt'))


    #Galesong Hill
        
                    if 'Falcon Coast' in line:
                        activity['details'] = "Traveling In Mondstadt"
                        activity['state'] = "Falcon Coast - Galesong Hill"
                        activity = switch_image_mode(activity, ('falconcoast', 'Traveling In Mondstadt'))
                 
                    if 'Reef' in line:
                        activity['details'] = "Traveling In Mondstadt"
                        activity['state'] = "Musk Reef - Mondstadt"
                        activity = switch_image_mode(activity, ('muskreef', 'Traveling In Mondstadt'))
                          
                    if 'Windrise' in line:
                        activity['details'] = "Traveling In Mondstadt"
                        activity['state'] = "Windrise - Galesong Hill"
                        activity = switch_image_mode(activity, ('windrise', 'Traveling In Mondstadt'))
 
                    if 'Cape Oath' in line:
                        activity['details'] = "Traveling In Mondstadt"
                        activity['state'] = "Cape Oath - Galesong Hill"
                        activity = switch_image_mode(activity, ('capeoath', 'Traveling In Mondstadt'))
                        
                    if 'aupa' in line:
                        activity['details'] = "Traveling In Mondstadt"
                        activity['state'] = "Daupa Gorge - Galesong Hill"
                        activity = switch_image_mode(activity, ('daupagorge', 'Traveling In Mondstadt'))

    #Windwail Highland

                    if 'Springvale' in line:
                        activity['details'] = "Traveling In Mondstadt"
                        activity['state'] = "Springvale - Windwail Highland"
                        activity = switch_image_mode(activity, ('springvale', 'Traveling In Mondstadt'))
                                                
                    if 'Dawn' in line:
                        activity['details'] = "Dawn Winery"
                        activity['state'] = "Dawn Winery - Windwail Highland"
                        activity = switch_image_mode(activity, ('dawnwinery', 'Traveling In Mondstadt'))
                                                
                    if 'Wolvedom' in line:
                        activity['details'] = "Traveling In Mondstadt"
                        activity['state'] = "Wolvedom - Windwail Highland"
                        activity = switch_image_mode(activity, ('wolvedom', 'Traveling In Mondstadt'))
   
    #Brightcrown Mountains
   
                    if 'Brightcrown Canyon' in line:
                        activity['details'] = "Traveling In Mondstadt"
                        activity['state'] = "Brightcrown Canyon - Brightcrown Mountains"
                        activity = switch_image_mode(activity, ('brightcrown Canyon', 'Traveling In Mondstadt'))
                                               
                    if 'Stormterror' in line:
                        activity['details'] = "Traveling In Mondstadt"
                        activity['state'] = "Stormterror's Lair - Brightcrown Mountains"
                        activity = switch_image_mode(activity, ('stormterror', 'Traveling In Mondstadt'))

#--------------------------------------------------------------------------------------

    # DragonSpine    
    
                    if 'Dragonspine' in line:
                        activity['details'] = "Traveling In Dragonspine"
                        activity['state'] = "Dragonspine"
                        activity = switch_image_mode(activity, ('dragonspine', 'Traveling In Dragonspine'))
                        
                    if 'Entombed City - Ancient Palace' in line:
                        activity['details'] = "Traveling In Dragonspine"
                        activity['state'] = "Entombed City - Ancient Palace - Dragonspine"
                        activity = switch_image_mode(activity, ('dragonspine', 'Traveling In Dragonspine'))
                                           
                    if 'Wyrmrest Valley' in line:
                        activity['details'] = "Traveling In Dragonspine"
                        activity['state'] = "Wyrmrest Valley - Dragonspine"
                        activity = switch_image_mode(activity, ('dragonspine', 'Traveling In Dragonspine'))
                                           
                    if 'Skyfrost Nail' in line:
                        activity['details'] = "Traveling In Dragonspine"
                        activity['state'] = "Skyfrost Nail - Dragonspine"
                        activity = switch_image_mode(activity, ('dragonspine', 'Traveling In Dragonspine'))
                                                               
                    if 'Starglow Cavern' in line:
                        activity['details'] = "Traveling In Dragonspine"
                        activity['state'] = "Starglow Cavern - Dragonspine"
                        activity = switch_image_mode(activity, ('dragonspine', 'Traveling In Dragonspine'))
                                                                                   
                    if 'Entombed City - Outskirts' in line:
                        activity['details'] = "Traveling In Dragonspine"
                        activity['state'] = "Entombed City - Outskirts - Dragonspine"
                        activity = switch_image_mode(activity, ('dragonspine', 'Traveling In Dragonspine'))
                    
#--------------------------------------------------------------------------------------

    # Liyue
    
    #Bishui Plain  
    
                    if 'Sal Terrae' in line:
                        activity['details'] = "Traveling In Liyue"
                        activity['state'] = "Sal Terrae - Bishui Plain"
                        activity = switch_image_mode(activity, ('liyue', 'Traveling In Liyue'))
                        
                    if 'Mingyun Village' in line:
                        activity['details'] = "Traveling In Liyue"
                        activity['state'] = "Mingyun Village - Bishui Plain"
                        activity = switch_image_mode(activity, ('liyue', 'Traveling In Liyue'))
                        
                    if 'Stone Gate' in line:
                        activity['details'] = "Traveling In Liyue"
                        activity['state'] = "Stone Gate - Bishui Plain"
                        activity = switch_image_mode(activity, ('liyue', 'Traveling In Liyue'))
                        
                    if 'Wuwang Hill' in line:
                        activity['details'] = "Traveling In Liyue"
                        activity['state'] = "Wuwang Hill - Bishui Plain"
                        activity = switch_image_mode(activity, ('liyue', 'Traveling In Liyue'))
                        
                            
                    if 'Quigce Village' in line:
                        activity['details'] = "Traveling In Liyue"
                        activity['state'] = "Quigce Village - Bishui Plain"
                        activity = switch_image_mode(activity, ('liyue', 'Traveling In Liyue'))
                        
                            
                    if 'Wangshu Inn' in line:
                        activity['details'] = "Traveling In Liyue"
                        activity['state'] = "Wangshu Inn - Bishui Plain"
                        activity = switch_image_mode(activity, ('liyue', 'Traveling In Liyue'))
                        
                            
                    if 'Guili Plains' in line:
                        activity['details'] = "Traveling In Liyue"
                        activity['state'] = "Guili Plains - Qiongji Estuary"
                        activity = switch_image_mode(activity, ('liyue', 'Traveling In Liyue'))
                        
                                
                    if 'Yaoguang Shoal' in line:
                        activity['details'] = "Traveling In Liyue"
                        activity['state'] = "Yaoguang Shoal - Qiongji Estuary"
                        activity = switch_image_mode(activity, ('liyue', 'Traveling In Liyue'))
                                       
                    if 'Luhua Pool' in line:
                        activity['details'] = "Traveling In Liyue"
                        activity['state'] = "Luhua Pool - Qiongji Estuary"
                        activity = switch_image_mode(activity, ('liyue', 'Traveling In Liyue'))
                             
                    if 'Cuijue Slope' in line:
                        activity['details'] = "Traveling In Liyue"
                        activity['state'] = "Cuijue Slope - Qiongji Estuary"
                        activity = switch_image_mode(activity, ('liyue', 'Traveling In Liyue'))
 
    #Minlin
    
                    if 'Jueyun Karst' in line:
                        activity['details'] = "Traveling In Liyue"
                        activity['state'] = "Jueyun Karst - Minlin"
                        activity = switch_image_mode(activity, ('liyue', 'Traveling In Liyue'))
                                 
                    if 'Qingyun Peak' in line:
                        activity['details'] = "Traveling In Liyue"
                        activity['state'] = "Qingyun Peak - Minlin"
                        activity = switch_image_mode(activity, ('liyue', 'Traveling In Liyue'))
              
                    if 'Mt. Aocang' in line:
                        activity['details'] = "Traveling In Liyue"
                        activity['state'] = "Mt. Aocang - Minlin"
                        activity = switch_image_mode(activity, ('liyue', 'Traveling In Liyue'))
                                                
                    if 'Huaguang Stone Forest' in line:
                        activity['details'] = "Traveling In Liyue"
                        activity['state'] = "Huaguang Stone Forest - Minlin"
                        activity = switch_image_mode(activity, ('liyue', 'Traveling In Liyue'))
                                                
                    if 'Mt. Hulao' in line:
                        activity['details'] = "Traveling In Liyue"
                        activity['state'] = "Mt. Hulao - Minlin"
                        activity = switch_image_mode(activity, ('liyue', 'Traveling In Liyue'))
                                                
                    if 'Nantianmen' in line:
                        activity['details'] = "Traveling In Liyue"
                        activity['state'] = "Nantianmen - Minlin"
                        activity = switch_image_mode(activity, ('liyue', 'Traveling In Liyue'))
                                                                        
                    if 'Tianqiu Valley' in line:
                        activity['details'] = "Traveling In Liyue"
                        activity['state'] = "Tianqiu Valley - Minlin"
                        activity = switch_image_mode(activity, ('liyue', 'Traveling In Liyue'))
 
    #Lisha    
 
                    if 'Dunyu Ruins' in line:
                        activity['details'] = "Traveling In Liyue"
                        activity['state'] = "Dunyu Ruins - Lisha"
                        activity = switch_image_mode(activity, ('liyue', 'Traveling In Liyue'))
                                                                                                                                        
                    if 'Quinxu Pool' in line:
                        activity['details'] = "Traveling In Liyue"
                        activity['state'] = "Quinxu Pool - Lisha"
                        activity = switch_image_mode(activity, ('liyue', 'Traveling In Liyue'))
                                                                                                                        
                    if 'Lingju Pass' in line:
                        activity['details'] = "Traveling In Liyue"
                        activity['state'] = "Lingju Pass - Lisha"
                        activity = switch_image_mode(activity, ('liyue', 'Traveling In Liyue'))
                        
    #Sea of Clouds
                         
                    if 'Guyun Stone Forest' in line:
                        activity['details'] = "Traveling In Liyue"
                        activity['state'] = "Guyun Stone Forest - Sea of Clouds"
                        activity = switch_image_mode(activity, ('liyue', 'Traveling In Liyue'))
                       
                    if 'Crux' in line:
                        activity['details'] = "Traveling In Liyue"
                        activity['state'] = "The Crux: The Alcor - Sea of Clouds"
                        activity = switch_image_mode(activity, ('liyue', 'Traveling In Liyue'))
                                                                                                                                                                                           
                    if 'Mt. Tianheng' in line:
                        activity['details'] = "Traveling In Liyue"
                        activity['state'] = "Mt. Tianheng - Sea of Clouds"
                        activity = switch_image_mode(activity, ('liyue', 'Traveling In Liyue'))
                                                                                                
                    if 'Liyue Harbor' in line:
                        activity['details'] = "Traveling In Liyue"
                        activity['state'] = "Liyue Harbor - Sea of Clouds"
                        activity = switch_image_mode(activity, ('liyue', 'Traveling In Liyue'))
                                                                                                
                    if 'Tianqiu Valley' in line:
                        activity['details'] = "Traveling In Liyue"
                        activity['state'] = "Tianqiu Valley - Liyue"
                        activity = switch_image_mode(activity, ('liyue', 'Traveling In Liyue'))
                                                                                                                        
                    if 'Jade Chamber' in line:
                        activity['details'] = "Traveling In Liyue"
                        activity['state'] = "Jade Chamber - Liyue"
                        activity = switch_image_mode(activity, ('liyue', 'Traveling In Liyue'))
                                                                                                              
                    if 'Lumberpick Valley' in line:
                        activity['details'] = "Traveling In Liyue"
                        activity['state'] = "Lumberpick Valley - The Chasm"
                        activity = switch_image_mode(activity, ('liyue', 'Traveling In Liyue'))

    #The Chasm
                                                                                                              
                    if 'Glaze Peak' in line:
                        activity['details'] = "Traveling In Liyue"
                        activity['state'] = "Glaze Peak - The Chasm"
                        activity = switch_image_mode(activity, ('chasm', 'Traveling In Liyue'))
                                                                                                                                            
                    if 'Fuao Vale' in line:
                        activity['details'] = "Traveling In Liyue"
                        activity['state'] = "Fuao Vale - The Chasm"
                        activity = switch_image_mode(activity, ('chasm', 'Traveling In Liyue'))
                                                                                                              
                    if 'Tiangong Gorge' in line:
                        activity['details'] = "Traveling In Liyue"
                        activity['state'] = "Tiangong Gorge - The Chasm"
                        activity = switch_image_mode(activity, ('chasm', 'Traveling In Liyue'))
                                                                                                              
                    if 'Cinnabar Cliff' in line:
                        activity['details'] = "Traveling In Liyue"
                        activity['state'] = "Cinnabar Cliff - The Chasm"
                        activity = switch_image_mode(activity, ('chasm', 'Traveling In Liyue'))
                                                                                                              
                    if 'The Chasm' in line:
                        activity['details'] = "Traveling In Liyue"
                        activity['state'] = "The Chasm's Maw - The Chasm"
                        activity = switch_image_mode(activity, ('chasm', 'Traveling In Liyue'))
                                                                                                              
                    if 'The Surface' in line:
                        activity['details'] = "Traveling In Liyue"
                        activity['state'] = "The Surface - The Chasm"
                        activity = switch_image_mode(activity, ('chasn', 'Traveling In Liyue'))

    #The Chasm: Underground Mines
                                                                                  
                    if 'Ad-Hoc Main Tunnel' in line:
                        activity['details'] = "Traveling In The Chasm: Underground Mines"
                        activity['state'] = "Ad-Hoc Main Tunnel - The Chasm: Underground Mines"
                        activity = switch_image_mode(activity, ('chasm', 'Traveling In Liyue'))
                                                                                                              
                    if 'Nameless Ruins' in line:
                        activity['details'] = "Traveling In The Chasm: Underground Mines"
                        activity['state'] = "Nameless Ruins - The Chasm: Underground Mines"
                        activity = switch_image_mode(activity, ('chasm', 'Traveling In Liyue'))
                                                                                                              
                    if 'Main Mining Area' in line:
                        activity['details'] = "Traveling In The Chasm: Underground Mines"
                        activity['state'] = "The Chasm: Main Mining Area - The Chasm: Underground Mines"
                        activity = switch_image_mode(activity, ('chasm', 'Traveling In Liyue'))
                                                                                                              
                    if 'The Glowing Narrows' in line:
                        activity['details'] = "Traveling In The Chasm: Underground Mines"
                        activity['state'] = "The Glowing Narrows - The Chasm: Underground Mines"
                        activity = switch_image_mode(activity, ('chasm', 'Traveling In The Chasm: Underground Mines'))
                                                                                                              
                    if 'Serpent' in line:
                        activity['details'] = "Traveling In The Chasm: Underground Mines"
                        activity['state'] = "The Serpent's Cave - The Chasm: Underground Mines"
                        activity = switch_image_mode(activity, ('chasm', 'Traveling In The Chasm: Underground Mines'))
                                                                                                              
                    if 'Underground Waterway' in line:
                        activity['details'] = "Traveling In The Chasm: Underground Mines"
                        activity['state'] = "Underground Waterway - The Chasm: Underground Mines"
                        activity = switch_image_mode(activity, ('chasm', 'Traveling In The Chasm: Underground Mines'))

#--------------------------------------------------------------------------------------

    # Inazuma
    
    #Narukami Island
    
                    if 'Inazuma City' in line:
                        activity['details'] = "Traveling In Inazuma"
                        activity['state'] = "Inazuma City - Narukami Island"
                        activity = switch_image_mode(activity, ('inazuma', 'Traveling In Inazuma'))
                        
                    if 'Byakko Plains' in line:
                        activity['details'] = "Traveling In Inazuma"
                        activity['state'] = "Byakko Plains - Narukami Island"
                        activity = switch_image_mode(activity, ('inazuma', 'Traveling In Inazuma'))
                        
                    if 'Konda Village' in line:
                        activity['details'] = "Traveling In Inazuma"
                        activity['state'] = "Konda Village - Narukami Island"
                        activity = switch_image_mode(activity, ('inazuma', 'Traveling In Inazuma'))
                        
                    if 'Amakane Island' in line:
                        activity['details'] = "Traveling In Inazuma"
                        activity['state'] = "Amakane Island - Narukami Island"
                        activity = switch_image_mode(activity, ('inazuma', 'Traveling In Inazuma'))

                    if 'Jiren Island' in line:
                        activity['details'] = "Traveling In Inazuma"
                        activity['state'] = "Jiren Island - Narukami Island"
                        activity = switch_image_mode(activity, ('inazuma', 'Traveling In Inazuma'))
                        
                    if 'Ritou' in line:
                        activity['details'] = "Traveling In Inazuma"
                        activity['state'] = "Ritou - Narukami Island"
                        activity = switch_image_mode(activity, ('inazuma', 'Traveling In Inazuma'))
                        
                    if 'Yougou' in line:
                        activity['details'] = "Traveling In Inazuma"
                        activity['state'] = "Mt. Yougou - Narukami Island"
                        activity = switch_image_mode(activity, ('inazuma', 'Traveling In Inazuma'))
                        
                    if 'Chinju Forest' in line:
                        activity['details'] = "Traveling In Inazuma"
                        activity['state'] = "Chinju Forest - Narukami Island"
                        activity = switch_image_mode(activity, ('inazuma', 'Traveling In Inazuma'))
                                                
                    if 'Grand Narukami Shrine' in line:
                        activity['details'] = "Traveling In Inazuma"
                        activity['state'] = "Grand Narukami Shrine - Narukami Island"
                        activity = switch_image_mode(activity, ('inazuma', 'Traveling In Inazuma'))   
                        
                    if 'Araumi' in line:
                        activity['details'] = "Traveling In Inazuma"
                        activity['state'] = "Araumi - Narukami Island"
                        activity = switch_image_mode(activity, ('inazuma', 'Traveling In Inazuma'))  
                                        
                    if 'Kamisato Estate' in line:
                        activity['details'] = "Traveling In Inazuma"
                        activity['state'] = "Kamisato Estate  - Narukami Island"
                        activity = switch_image_mode(activity, ('inazuma', 'Traveling In Inazuma'))  
    
    #Kannazuka
    
                    if 'Encampment' in line:
                        activity['details'] = "Traveling In Inazuma"
                        activity['state'] = "Kujou Encampment - Kannazuka"
                        activity = switch_image_mode(activity, ('inazuma', 'Traveling In Inazuma'))                          
                                            
                    if 'rasuna' in line:
                        activity['details'] = "Traveling In Inazuma"
                        activity['state'] = "Tatarasuna - Kannazuka"
                        activity = switch_image_mode(activity, ('inazuma', 'Traveling In Inazuma'))   
                                                                        
                    if 'Nazuchi Beach' in line:
                        activity['details'] = "Traveling In Inazuma"
                        activity['state'] = "Nazuchi Beach - Kannazuka"
                        activity = switch_image_mode(activity, ('inazuma', 'Traveling In Inazuma'))   
    
    #Yashiori Island
    
                    if 'Musoujin Gorge' in line:
                        activity['details'] = "Traveling In Inazuma"
                        activity['state'] = "Musoujin Gorge - Yashiori Island"
                        activity = switch_image_mode(activity, ('inazuma', 'Traveling In Inazuma'))  
                                      
                    if 'Fujitou' in line:
                        activity['details'] = "Traveling In Inazuma"
                        activity['state'] = "Fort Fujitou - Yashiori Island"
                        activity = switch_image_mode(activity, ('inazuma', 'Traveling In Inazuma')) 
                                                   
   
                    if 'Higi' in line:
                        activity['details'] = "Traveling In Inazuma"
                        activity['state'] = "Higi Village - Yashiori Island"
                        activity = switch_image_mode(activity, ('inazuma', 'Traveling In Inazuma'))                          
                               
                    if 'Higi Village' in line:
                        activity['details'] = "Traveling In Inazuma"
                        activity['state'] = "Higi Village - Yashiori Island"
                        activity = switch_image_mode(activity, ('inazuma', 'Traveling In Inazuma'))                          
                                                 
                             
                    if 'Head' in line:
                        activity['details'] = "Traveling In Inazuma"
                        activity['state'] = "Serpent's Head - Yashiori Island"
                        activity = switch_image_mode(activity, ('inazuma', 'Traveling In Inazuma'))    
    
                    if 'Jakotsu' in line:
                        activity['details'] = "Traveling In Inazuma"
                        activity['state'] = "Jakotsu Mine - Yashiori Island"
                        activity = switch_image_mode(activity, ('inazuma', 'Traveling In Inazuma')) 
                        
                    if 'Jakotsu Mine' in line:
                        activity['details'] = "Traveling In Inazuma"
                        activity['state'] = "Jakotsu Mine - Yashiori Island"
                        activity = switch_image_mode(activity, ('inazuma', 'Traveling In Inazuma')) 
                        
                    if 'Mumei' in line:
                        activity['details'] = "Traveling In Inazuma"
                        activity['state'] = "Fort Mumei - Yashiori Island"
                        activity = switch_image_mode(activity, ('inazuma', 'Traveling In Inazuma'))  

    #Watatsumi Island

                    if 'Borou Village' in line:
                        activity['details'] = "Traveling In Inazuma"
                        activity['state'] = "Bourou Village - Watatsumi Island"
                        activity = switch_image_mode(activity, ('inazuma', 'Traveling In Inazuma'))   
                        
                    if 'Bourouw' in line:
                        activity['details'] = "Traveling In Inazuma"
                        activity['state'] = "Bourou Village - Watatsumi Island"
                        activity = switch_image_mode(activity, ('inazuma', 'Traveling In Inazuma'))     
                                                
                    if 'Bourou' in line:
                        activity['details'] = "Traveling In Inazuma"
                        activity['state'] = "Bourou Village - Watatsumi Island"
                        activity = switch_image_mode(activity, ('inazuma', 'Traveling In Inazuma'))     
                        
                    if 'Sangonomiya' in line:
                        activity['details'] = "Traveling In Inazuma"
                        activity['state'] = "Sangonomiya Shrine - Watatsumi Island"
                        activity = switch_image_mode(activity, ('inazuma', 'Traveling In Inazuma'))  
                        
                    if 'Sangonomiya Shrine' in line:
                        activity['details'] = "Traveling In Inazuma"
                        activity['state'] = "Sangonomiya Shrine - Watatsumi Island"
                        activity = switch_image_mode(activity, ('inazuma', 'Traveling In Inazuma'))  
                        
                    if 'Mouun' in line:
                        activity['details'] = "Traveling In Inazuma"
                        activity['state'] = "Mouun Shrine - Watatsumi Island"
                        activity = switch_image_mode(activity, ('inazuma', 'Traveling In Inazuma'))  
                        
                    if 'Mouun Shrine' in line:
                        activity['details'] = "Traveling In Inazuma"
                        activity['state'] = "Mouun Shrine - Watatsumi Island"
                        activity = switch_image_mode(activity, ('inazuma', 'Traveling In Inazuma'))  

                    if 'Suigetsu Pool' in line:
                        activity['details'] = "Traveling In Inazuma"
                        activity['state'] = "Suigetsu Pool - Watatsumi Island"
                        activity = switch_image_mode(activity, ('inazuma', 'Traveling In Inazuma'))  
                        
                    if 'Suigetsu' in line:
                        activity['details'] = "Traveling In Inazuma"
                        activity['state'] = "Suigetsu Pool - Watatsumi Island"
                        activity = switch_image_mode(activity, ('inazuma', 'Traveling In Inazuma'))  
                        
    #Seirai Island
    
                    if 'Hiraumi' in line:
                        activity['details'] = "Traveling In Inazuma"
                        activity['state'] = "Fort Hiraumi - Seirai Island"
                        activity = switch_image_mode(activity, ('inazuma', 'Traveling In Inazuma'))  
                        
                    if 'Fort Hiraumi' in line:
                        activity['details'] = "Traveling In Inazuma"
                        activity['state'] = "Fort Hiraumi - Seirai Island"
                        activity = switch_image_mode(activity, ('inazuma', 'Traveling In Inazuma'))  
                        
                    if 'Koseki' in line:
                        activity['details'] = "Traveling In Inazuma"
                        activity['state'] = "Koseki Village - Seirai Island"
                        activity = switch_image_mode(activity, ('inazuma', 'Traveling In Inazuma'))  
                        
                    if 'Koseki Village' in line:
                        activity['details'] = "Traveling In Inazuma"
                        activity['state'] = "Koseki Village - Seirai Island"
                        activity = switch_image_mode(activity, ('inazuma', 'Traveling In Inazuma'))  

                    if 'Seiraimaru' in line:
                        activity['details'] = "Traveling In Inazuma"
                        activity['state'] = "Seiraimaru - Seirai Island"
                        activity = switch_image_mode(activity, ('inazuma', 'Traveling In Inazuma'))  
                        

                    if 'Asase' in line:
                        activity['details'] = "Traveling In Inazuma"
                        activity['state'] = "Asase Shrine - Seirai Island"
                        activity = switch_image_mode(activity, ('inazuma', 'Traveling In Inazuma'))  
                        
                    if 'Asase Shrine' in line:
                        activity['details'] = "Traveling In Inazuma"
                        activity['state'] = "Asase Shrine - Seirai Island"
                        activity = switch_image_mode(activity, ('inazuma', 'Traveling In Inazuma'))      

                    if 'Amakumo' in line:
                        activity['details'] = "Traveling In Inazuma"
                        activity['state'] = "Amakumo Peak - Seirai Island"
                        activity = switch_image_mode(activity, ('inazuma', 'Traveling In Inazuma'))  
                        
                    if 'Amakumo Peak' in line:
                        activity['details'] = "Traveling In Inazuma"
                        activity['state'] = "Amakumo Peak - Seirai Island"
                        activity = switch_image_mode(activity, ('inazuma', 'Traveling In Inazuma'))  
   
    #Tsurumi Island
    
                    if 'Autake Plains' in line:
                        activity['details'] = "Traveling In Inazuma"
                        activity['state'] = "Autake Plains - Tsurumi Island"
                        activity = switch_image_mode(activity, ('inazuma', 'Traveling In Inazuma'))  
                                                
                    if 'Chirai Shrine' in line:
                        activity['details'] = "Traveling In Inazuma"
                        activity['state'] = "Chirai Shrine - Tsurumi Island"
                        activity = switch_image_mode(activity, ('inazuma', 'Traveling In Inazuma'))  
                                                
                    if 'Moshiri Ceremonial Site' in line:
                        activity['details'] = "Traveling In Inazuma"
                        activity['state'] = "Moshiri Ceremonial Site - Tsurumi Island"
                        activity = switch_image_mode(activity, ('inazuma', 'Traveling In Inazuma'))  
                                                
                    if 'Mt. Kanna' in line:
                        activity['details'] = "Traveling In Inazuma"
                        activity['state'] = "Mt. Kanna - Tsurumi Island"
                        activity = switch_image_mode(activity, ('inazuma', 'Traveling In Inazuma'))  
                                                                        
                    if 'Oina Beach' in line:
                        activity['details'] = "Traveling In Inazuma"
                        activity['state'] = "Oina Beach - Tsurumi Island"
                        activity = switch_image_mode(activity, ('inazuma', 'Traveling In Inazuma'))  
                                                                        
                    if 'Shirikoro Peak' in line:
                        activity['details'] = "Traveling In Inazuma"
                        activity['state'] = "Shirikoro Peak - Tsurumi Island"
                        activity = switch_image_mode(activity, ('inazuma', 'Traveling In Inazuma'))  
                                                                        
                    if 'Wakukau Shoal' in line:
                        activity['details'] = "Traveling In Inazuma"
                        activity['state'] = "Wakukau Shoal - Tsurumi Island"
                        activity = switch_image_mode(activity, ('inazuma', 'Traveling In Inazuma'))  
 
#--------------------------------------------------------------------------------------

    # Enkanomiya
                                                                        
                    if 'Dainichi Mikoshi' in line:
                        activity['details'] = "Traveling In Enkanomiya"
                        activity['state'] = "Dainichi Mikoshi - Enkanomiya"
                        activity = switch_image_mode(activity, ('enkanomiya', 'Traveling In Enkanomiya'))  
                                                                         
                    if 'Evernight Temple' in line:
                        activity['details'] = "Traveling In Enkanomiya"
                        activity['state'] = "Evernight Temple - Tsurumi Island"
                        activity = switch_image_mode(activity, ('enkanomiya', 'Traveling In Enkanomiya'))  
                                                                         
                    if 'The Narrows' in line:
                        activity['details'] = "Traveling In Enkanomiya"
                        activity['state'] = "The Narrows - Tsurumi Island"
                        activity = switch_image_mode(activity, ('enkanomiya', 'Traveling In Enkanomiya'))  
                                                                         
                    if 'Bowels' in line:
                        activity['details'] = "Traveling In Enkanomiya"
                        activity['state'] = "The Serpent's Bowels - Tsurumi Island"
                        activity = switch_image_mode(activity, ('enkanomiya', 'Traveling In Enkanomiya'))  
                                                                         
                    if 'Heart' in line:
                        activity['details'] = "Traveling In Enkanomiya"
                        activity['state'] = "The Serpent's Heart - Tsurumi Island"
                        activity = switch_image_mode(activity, ('enkanomiya', 'Traveling In Enkanomiya'))  
                                                                          
                    if 'Yachimatahiko' in line:
                        activity['details'] = "Traveling In Enkanomiya"
                        activity['state'] = "Yachimatahiko's Locus - Tsurumi Island"
                        activity = switch_image_mode(activity, ('enkanomiya', 'Traveling In Enkanomiya'))  
                                                                           
                    if 'Yachimatahime' in line:
                        activity['details'] = "Traveling In Enkanomiya"
                        activity['state'] = "Yachimatahime's Locus - Tsurumi Island"
                        activity = switch_image_mode(activity, ('enkanomiya', 'Traveling In Enkanomiya'))  
                                                                           
                    if 'Kunado' in line:
                        activity['details'] = "Traveling In Enkanomiya"
                        activity['state'] = "Kunado's Locus - Tsurumi Island"
                        activity = switch_image_mode(activity, ('enkanomiya', 'Traveling In Enkanomiya'))  
                        
 #--------------------------------------------------------------------------------------

    # Weekly Bosses

                    if 'Dvalin' in line:
                        activity['details'] = "Currently Fighting a Boss"
                        activity['state'] = "Stormterror Dvalin - Erstwhile King of the Skies"
                        activity = switch_image_mode(activity, ('dvalin', 'Currently Fighting a Boss'))  
                        
                    if 'Childe' in line:
                        activity['details'] = "Currently Fighting a Boss"
                        activity['state'] = "Childe - Eleventh of the Fatui Harbringers" 
                        activity = switch_image_mode(activity, ('childe', 'Currently Fighting a Boss'))  
                        
                    if 'Azhdaha' in line:
                        activity['details'] = "Currently Fighting a Boss"
                        activity['state'] = "Azhdaha - Sealed Lord of Vishaps"
                        activity = switch_image_mode(activity, ('azhdaha', 'Currently Fighting a Boss'))     
                                
                    if 'Signora' in line:
                        activity['details'] = "Currently Fighting a Boss"
                        activity['state'] = "La Signora - Eight of the Fatui Harbringers"
                        activity = switch_image_mode(activity, ('signora', 'Currently Fighting a Boss'))     
                                
                    if 'Magatsu Mitake Narukami no Mikoto' in line:
                        activity['details'] = "Currently Fighting a Boss"
                        activity['state'] = "Magatsu Mitake Narukami no Mikoto - Raiden no Inazuma tono"
                        activity = switch_image_mode(activity, ('magatsu_mitake_narukami_no_mikoto', 'Currently Fighting a Boss'))     

    # Cube Bosses
    
                    if 'Anemo Hypostasis' in line:
                        activity['details'] = "Currently Fighting a Boss"
                        activity['state'] = "Anemo Hypostasis - Beth"
                        activity = switch_image_mode(activity, ('bossplaceholder', 'Currently Fighting a Boss'))  
                            
                    if 'Electro Hypostasis' in line:
                        activity['details'] = "Currently Fighting a Boss"
                        activity['state'] = "Electro Hypostasis - Aleph"
                        activity = switch_image_mode(activity, ('bossplaceholder', 'Currently Fighting a Boss'))  
                            
                    if 'Cryo Hypostasis' in line:
                        activity['details'] = "Currently Fighting a Boss"
                        activity['state'] = "Cryo Hypostasis - Daleth"
                        activity = switch_image_mode(activity, ('bossplaceholder', 'Currently Fighting a Boss'))  
                            
                    if 'Geo Hypostasis' in line:
                        activity['details'] = "Currently Fighting a Boss"
                        activity['state'] = "Geo Hypostasis - Gimel"
                        activity = switch_image_mode(activity, ('bossplaceholder', 'Currently Fighting a Boss'))  
                                                    
                    if 'Pyro Hypostasis' in line:
                        activity['details'] = "Currently Fighting a Boss"
                        activity['state'] = "Pyro Hypostasis - Ayin Bellowing Blaze"
                        activity = switch_image_mode(activity, ('bossplaceholder', 'Currently Fighting a Boss'))  
                                                                         
                    if 'Hydro Hypostasis' in line:
                        activity['details'] = "Currently Fighting a Boss"
                        activity['state'] = "Hydro Hypostasis - He"
                        activity = switch_image_mode(activity, ('bossplaceholder', 'Currently Fighting a Boss'))  
                        
    # Flower Bosses
    
                    if 'Cryo Regisvine' in line:
                        activity['details'] = "Currently Fighting a Boss"
                        activity['state'] = "Cryo Regisvine - Silent Frost Bloom"
                        activity = switch_image_mode(activity, ('bossplaceholder', 'Currently Fighting a Boss'))  
    
                    if 'Pyro Regisvine' in line:
                        activity['details'] = "Currently Fighting a Boss"
                        activity['state'] = "Pyro Regisvine - Flickering Blaze Bloom"
                        activity = switch_image_mode(activity, ('bossplaceholder', 'Currently Fighting a Boss'))  
                        
    # Mechanical Bosses 
    
                    if 'Ruin Serpent' in line:
                        activity['details'] = "Currently Fighting a Boss"
                        activity['state'] = "Ruin Serpent - Excavator: SI/Glp"
                        activity = switch_image_mode(activity, ('bossplaceholder', 'Currently Fighting a Boss'))  
        
                    if 'Perpetual Mechanical Array' in line:
                        activity['details'] = "Currently Fighting a Boss"
                        activity['state'] = "Perpetual Mechanical Array - Perpetual Resonance SI/Ald"
                        activity = switch_image_mode(activity, ('bossplaceholder', 'Currently Fighting a Boss'))  
                        
                    if 'Maguu Kenki' in line:
                        activity['details'] = "Currently Fighting a Boss"
                        activity['state'] = "Maguu Kenki - Ingenious Machine: Marionette Swordmaster"
                        activity = switch_image_mode(activity, ('bossplaceholder', 'Currently Fighting a Boss'))  
                   
    # Doggo Bosses 

                    if 'Andrius' in line:
                        activity['details'] = "Currently Fighting a Boss"
                        activity['state'] = "Andrius - Dominator of Wolves"
                        activity = switch_image_mode(activity, ('bossplaceholder', 'Currently Fighting a Boss'))  
                       
                    if 'Golden Wolflord' in line:
                        activity['details'] = "Currently Fighting a Boss"
                        activity['state'] = "Golden Wolflord - Nameless King of the Rift"
                        activity = switch_image_mode(activity, ('bossplaceholder', 'Currently Fighting a Boss'))  

    # Birb Bosses 
                        
                    if 'Rhodeia of Loch' in line:
                        activity['details'] = "Currently Fighting a Boss"
                        activity['state'] = "Rhodeia of Loch - Oceanid of Quigce"
                        activity = switch_image_mode(activity, ('bossplaceholder', 'Currently Fighting a Boss'))  
                                           
                    if 'Thunder Manifestation' in line:
                        activity['details'] = "Currently Fighting a Boss"
                        activity['state'] = "Thunder Manifestation - Raging Thunder of Amakuno Peak"
                        activity = switch_image_mode(activity, ('bossplaceholder', 'Currently Fighting a Boss'))  
                   
    # Other Bosses
                                           
                    if 'Coral Defenders' in line:
                        activity['details'] = "Currently Fighting a Boss"
                        activity['state'] = "Coral Defenders - Bathysmal Vishap Herd"
                        activity = switch_image_mode(activity, ('bossplaceholder', 'Currently Fighting a Boss'))  
                   
                                                                         
                    if 'Primo Geovishap' in line:
                        activity['details'] = "Currently Fighting a Boss"
                        activity['state'] = "Primo Geovishap - Geo Dragon Who Once Raged With the King Long-Slumbering Earthshaker Dragon"
                        activity = switch_image_mode(activity, ('bossplaceholder', 'Currently Fighting a Boss'))  
                   
                                               

    
#--------------------------------------------------------------------------------------
##rich presence stuff

            if time.time() - start_time < 10:
                activity['details'] = "Loading game"
                activity = switch_image_mode(activity, ('title', 'Loading game'))

            if old_details_state != (activity['details'], activity['state'], activity['assets']['small_image'], activity['assets']['small_text']):
                next_delay = 2

            print(activity['details'])
            print(activity['state'])
            print(activity['assets']['small_image'])
            print(activity['assets']['small_text'])
            
            time_elapsed = time.time() - start_time
            print("{:02}:{:02} elapsed\n".format(int(time_elapsed / 60), round(time_elapsed % 60)))

            if not os.path.exists('history.txt'):
                open('history.txt', 'w').close()

            activity_str = f'{activity}\n'
            with open('history.txt', 'r') as history_file_r:
                history = history_file_r.readlines()
            if activity_str not in history:
                with open('history.txt', 'a') as history_file_a:
                    history_file_a.write(activity_str)
                    
            # send everything to discord
            client.update_activity(activity)
        elif not discord_is_running:
            print("{}\nDiscord isn't running\n")
        else:
            if client_connected:
                try:
                    client.disconnect()  # doesn't work...
                except:
                    pass

                raise SystemExit  # ...but this does
            else:
                if not has_mention_not_running:
                    print("Genshin Impact isn't running\n")
                    has_mention_not_running = True

            # to prevent connecting when already connected
            client_connected = False

        time.sleep(next_delay)


def switch_image_mode(temp_activity, stage=()):
    if stage == ():
        temp_activity['assets']['large_text'] = 'Genshin Impact'
    else:
        temp_activity['assets']['large_image'] = stage[0]
        temp_activity['assets']['large_text'] = stage[1]
        temp_activity['details'] = stage[+1]

    return temp_activity

if __name__ == '__main__':
    main()