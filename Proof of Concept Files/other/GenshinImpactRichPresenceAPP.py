import customtkinter
import os
from PIL import Image
import subprocess

def Install():
    subprocess.Popen('InstallRichPresence.bat')
    
def Start():
    subprocess.Popen('StartRichPresence.bat')

    
def Stop():
    subprocess.call(["taskkill","/F","/IM","python.exe"])
    subprocess.call(["taskkill","/F","/IM","py.exe"])    
    subprocess.call(["taskkill","/F","/IM","GenshinImpactRichPresenceAPP.exe"])    


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.title("Genshin Impact Rich Presence v2.5.1")
        self.geometry("800x500")
        self.iconbitmap('ApplicationIcon.ico')
        # set grid layout 1x2
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # load images with light and dark mode image
        image_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "App-Images")
        self.logo_image = customtkinter.CTkImage(Image.open(os.path.join(image_path, "ApplicationIcon.png")), size=(50, 50))
        self.large_test_image = customtkinter.CTkImage(Image.open(os.path.join(image_path, "StarSnatchCliff.png")), size=(400, 200))
        self.image_icon_image = customtkinter.CTkImage(Image.open(os.path.join(image_path, "image_icon_light.png")), size=(50, 50))
        self.home_image = customtkinter.CTkImage(light_image=Image.open(os.path.join(image_path, "Home.png")), size=(50, 50))
        self.settings_image = customtkinter.CTkImage(light_image=Image.open(os.path.join(image_path, "Icon Character Archive.png")), size=(50, 50))
        self.info_image = customtkinter.CTkImage(light_image=Image.open(os.path.join(image_path, "Info.png")), size=(50, 50))
        self.start_image = customtkinter.CTkImage(light_image=Image.open(os.path.join(image_path, "Icon Archive Geography.png")), size=(50, 50))
        self.stop_image = customtkinter.CTkImage(light_image=Image.open(os.path.join(image_path, "Icon Stop.png")), size=(50, 50))
        self.install_image = customtkinter.CTkImage(light_image=Image.open(os.path.join(image_path, "Icon Archon Quests.png")), size=(50, 50))
        self.apply_image = customtkinter.CTkImage(light_image=Image.open(os.path.join(image_path, "Info.png")), size=(50, 50))

        # create navigation frame
        self.navigation_frame = customtkinter.CTkFrame(self, corner_radius=0)
        self.navigation_frame.grid(row=0, column=0, sticky="nsew")
        self.navigation_frame.grid_rowconfigure(4, weight=1)

        self.navigation_frame_label = customtkinter.CTkLabel(self.navigation_frame, text="  Genshin Impact Rich Presence", image=self.logo_image,
                                                             compound="left", font=customtkinter.CTkFont(size=12, weight="bold"))
        self.navigation_frame_label.grid(row=0, column=0, padx=20, pady=20)

        self.home_button = customtkinter.CTkButton(self.navigation_frame, corner_radius=0, height=40, border_spacing=10, text="Rich Presence Control",
                                                   fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                                   image=self.home_image, anchor="w", command=self.home_button_event, font=customtkinter.CTkFont(size=12, weight="bold"))
        self.home_button.grid(row=1, column=0, sticky="ew")

        self.frame_2_button = customtkinter.CTkButton(self.navigation_frame, corner_radius=0, height=40, border_spacing=10, text="WIP(Not Implemented yet)",
                                                      fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                                      image=self.settings_image, anchor="w", command=self.frame_2_button_event, font=customtkinter.CTkFont(size=12, weight="bold"))
        self.frame_2_button.grid(row=2, column=0, sticky="ew")

        self.frame_3_button = customtkinter.CTkButton(self.navigation_frame, corner_radius=0, height=40, border_spacing=10, text="Info",
                                                      fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                                      image=self.info_image, anchor="w", command=self.frame_3_button_event, font=customtkinter.CTkFont(size=12, weight="bold"))
        self.frame_3_button.grid(row=3, column=0, sticky="ew")

        self.appearance_mode_menu = customtkinter.CTkOptionMenu(self.navigation_frame, values=["Dark", "Light", "System"],
                                                                command=self.change_appearance_mode_event)
        self.appearance_mode_menu.grid(row=6, column=0, padx=20, pady=20, sticky="s")

        # create home frame
        self.home_frame = customtkinter.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.home_frame.grid_columnconfigure(0, weight=1)

        self.home_frame_large_image_label = customtkinter.CTkLabel(self.home_frame, text="", image=self.large_test_image)
        self.home_frame_large_image_label.grid(row=0, column=0, padx=20, pady=10)
        
        home_frame_button_2 = customtkinter.CTkButton(self.home_frame, text="Start Discord Rich Presence",
                                                           fg_color="gray30", hover_color=("green", "green"), image=self.start_image, compound="right",
                                                           command=Start, font=customtkinter.CTkFont(size=12, weight="bold"))
        home_frame_button_2.grid(row=1, column=0, padx=20, pady=10)
        
        home_frame_button_3 = customtkinter.CTkButton(self.home_frame, text="Stop Discord Rich Presence", fg_color="gray30", hover_color=("red", "red"), image=self.stop_image, compound="right",
                                                           command=Stop, font=customtkinter.CTkFont(size=12, weight="bold"))
        home_frame_button_3.grid(row=2, column=0, padx=20, pady=10)
        
        home_frame_button_2 = customtkinter.CTkButton(self.home_frame, text="Install Discord Rich Presence (if you haven't already)", image=self.install_image, compound="right",
                                                           command=Install, font=customtkinter.CTkFont(size=12, weight="bold"))
        home_frame_button_2.grid(row=3, column=0, padx=20, pady=10)

        # create second frame
        
        self.second_frame = customtkinter.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.second_frame.grid_columnconfigure(0, weight=1)
        
        second_frame_large_image_label = customtkinter.CTkLabel(self.second_frame, text="", image=self.large_test_image)
        second_frame_large_image_label.grid(row=1, column=0, padx=20, pady=10)
                
        second_frame_label = customtkinter.CTkLabel(self.second_frame, text="(not working yet)Character and Resolution Settings", font=customtkinter.CTkFont(size=12, weight="bold"))
        second_frame_label.grid(row=2, column=0, padx=20, pady=10)

        second_frame_entry_1 = customtkinter.CTkEntry(self.second_frame, placeholder_text="(not working yet)Your Name Here", width=400)
        second_frame_entry_1.grid(row=3, column=0, padx=20, pady=10)

        second_frame_entry_2 = customtkinter.CTkEntry(self.second_frame, placeholder_text="(not working yet)Your Wanderer Name Here", width=400)
        second_frame_entry_2.grid(row=4, column=0, padx=20, pady=10)
        
        second_frame_entry_3 = customtkinter.CTkEntry(self.second_frame, placeholder_text="(not working yet)Your Resolution (Example= 1920x1080, 1080p should be written)", width=400)
        second_frame_entry_3.grid(row=5, column=0, padx=20, pady=10)
        
        second_frame_button_2 = customtkinter.CTkButton(self.second_frame, text="(not working yet)Apply", image=self.image_icon_image, compound="right",font=customtkinter.CTkFont(size=12, weight="bold"))
        second_frame_button_2.grid(row=7, column=0, padx=20, pady=10)
        
        # create third frame
        self.third_frame = customtkinter.CTkFrame(self, corner_radius=0, fg_color="transparent")
        
        self.third_frame_label = customtkinter.CTkLabel(self.third_frame, text="Rich Presence created by ZANdewanai and rewritten by euwbah", corner_radius=400, font=customtkinter.CTkFont(size=12, weight="bold"))
        self.third_frame_label.grid(row=2, column=0, padx=20, pady=10)
        
        self.third_frame_label = customtkinter.CTkLabel(self.third_frame, text="Image assets are intellectual property of HoYoverse", width=400, font=customtkinter.CTkFont(size=12, weight="bold"))
        self.third_frame_label.grid(row=3, column=0, padx=20, pady=10)
        
        self.third_frame_label = customtkinter.CTkLabel(self.third_frame, text="© All rights reserved by miHoYo", width=400, font=customtkinter.CTkFont(size=12, weight="bold"))
        self.third_frame_label.grid(row=4, column=0, padx=20, pady=10)

        # select default frame
        self.select_frame_by_name("home")

        
    def select_frame_by_name(self, name):
        # set button color for selected button
        self.home_button.configure(fg_color=("gray75", "gray25") if name == "home" else "transparent")
        self.frame_2_button.configure(fg_color=("gray75", "gray25") if name == "frame_2" else "transparent")
        self.frame_3_button.configure(fg_color=("gray75", "gray25") if name == "frame_3" else "transparent")

        # show selected frame
        if name == "home":
            self.home_frame.grid(row=0, column=1, sticky="nsew")
        else:
            self.home_frame.grid_forget()
        if name == "frame_2":
            self.second_frame.grid(row=0, column=1, sticky="nsew")
        else:
            self.second_frame.grid_forget()
        if name == "frame_3":
            self.third_frame.grid(row=0, column=1, sticky="nsew")
        else:
            self.third_frame.grid_forget()

    def home_button_event(self):
        self.select_frame_by_name("home")

    def frame_2_button_event(self):
        self.select_frame_by_name("frame_2")

    def frame_3_button_event(self):
        self.select_frame_by_name("frame_3")
        
    def change_appearance_mode_event(self, new_appearance_mode):
      customtkinter.set_appearance_mode(new_appearance_mode)
      

if __name__ == "__main__":
    app = App()
    app.mainloop()

