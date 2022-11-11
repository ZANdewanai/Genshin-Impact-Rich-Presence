import tkinter
from tkinter import messagebox
import subprocess
import os 


# Handle errors while calling os.ulink()
window = tkinter.Tk()
window.title("Genshin Impact Rich Presence 1440p Ver")
window.geometry("400x500")
window.iconbitmap(default='images\\ApplicatonIcon.ico')
window.resizable(0, 0)
window.config(bg="black") 



def Start():
    subprocess.Popen('GrabParty1440p.exe'),
    subprocess.Popen('GrabArea1440p.exe')
    subprocess.Popen('RichPresence.bat')

    
def Stop():
    subprocess.call(["taskkill","/F","/IM","GrabParty1440p.exe"])
    subprocess.call(["taskkill","/F","/IM","GrabArea1440p.exe"])    
    os.remove("player.log")
    
myimage = tkinter.PhotoImage(file="images\\StarSnatchCliff.png")

image = tkinter.Label(window, image=myimage, width=600, height=200, )
image.pack()

button = tkinter.Button(text="Start Discord Rich Presence 1440p Ver", command=Start)
button.pack(pady=10)

button = tkinter.Button(text="Stop Grabbing Genshin Impact Names (the 2 windows that opened)", command=Stop)
button.pack(pady=10)

button = tkinter.Button(text="to stop the Discord Rich Presence close this application and CMD Window that appeared",
                       bg="black",
                       fg="white")      
button.pack(pady=10)


window.mainloop()   