import tkinter
from tkinter import messagebox
import subprocess
import tkinter.font as font


# Handle errors while calling os.ulink()
window = tkinter.Tk()
window.title("Genshin Impact Rich Presence")
window.geometry("800x600")
window.iconbitmap(default='images\\ApplicatonIcon.ico')
window.resizable(800, 600)
window.config(bg="white") 

myFont = font.Font(size=12)

def Install():
    subprocess.Popen('InstallRichPresence.bat')
    
def Start():
    subprocess.Popen('StartRichPresence.bat')

    
def Stop():
    subprocess.call(["taskkill","/F","/IM","python.exe"])
    subprocess.call(["taskkill","/F","/IM","py.exe"])    
    subprocess.call(["taskkill","/F","/IM","GenshinImpactRichPresenceAPP.exe"])    

myimage = tkinter.PhotoImage(file="images\\StarSnatchCliff3.png")

image = tkinter.Label(window, image=myimage, width=800, height=-400)
image.pack()


button = tkinter.Button(text="Start Discord Rich Presence", command=Start)
button.pack(pady=10)
button['font'] = myFont

button = tkinter.Button(text="Stop Rich Presence and Close This App ( it will open 3 cmd windows to stop python and this app)",command=Stop,
                       bg="black",
                       fg="white")      
button.pack(pady=10)
button['font'] = myFont

button = tkinter.Button(text="Install and Start Discord Rich Presence (if you havent already)",command=Install,
                       bg="blue",
                       fg="white")      
button.pack(pady=10)
button['font'] = myFont


window.mainloop()   