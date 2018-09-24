 #--------------------------------------------------------
 # import
 #--------------------------------------------------------
import os
import shutil
import glob
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as tkmsg
import tkinter.filedialog as tkfd
import cv2
import numpy as np
 #--------------------------------------------------------
 # defines
 #--------------------------------------------------------
MAIN_DISPLAY_SIZE = "900x750"

 #--------------------------------------------------------
 # functions
 #--------------------------------------------------------
def make_rgb(img):
    # expect img is [r,g,b]
    r, b, g = img.copy(), img.copy(), img.copy()
    r[:,:,[1,2]] = 0
    g[:,:,[0,2]] = 0
    b[:,:,[0,1]] = 0

    return r, g, b

def make_yuv(img):
    # expect img is [r,g,b]
    def LUT_U():
        # [r,g,b]
        return np.array([[[0,255-i,i] for i in range(256)]],dtype=np.uint8)
    def LUT_V():
        # [r,g,b]
        return np.array([[[i,255-i,0] for i in range(256)]],dtype=np.uint8)

    img_yuv = cv2.cvtColor(img, cv2.COLOR_RGB2YUV)
    y, u, v = cv2.split(img_yuv)

    y = cv2.cvtColor(y, cv2.COLOR_GRAY2RGB)
    u = cv2.cvtColor(u, cv2.COLOR_GRAY2RGB)
    v = cv2.cvtColor(v, cv2.COLOR_GRAY2RGB)

    u = cv2.LUT(u, LUT_U())
    v = cv2.LUT(v, LUT_V())

    return y, u, v

class ImageViewer():
    CANVAS_WIDTH = 640
    CANVAS_HEIGHT = 640
    IMG_SIZE = (640,480)

    def __init__(self, master):
        self.parent = master
        self.parent.title("RGB_YUV_Viewer")
        self.parent.resizable(width=tk.TRUE, height=tk.TRUE)
        self.parent.bind("<Left>", self.prev)
        self.parent.bind("<Right>", self.next)

        self.init_menubar()
        self.init_imageviewer()

    def init_menubar(self):
        menubar = tk.Menu(self.parent)
        self.parent.configure(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=False)
        menubar.add_cascade(label="Dir", underline=0, menu=file_menu)
        file_menu.add_command(label="Open", underline=0, command=self.open_dir)


    def init_imageviewer(self):
        self.image_paths = list() # image abs_paths
        # dirs
        self.root_dir = None
        self.image_dir = None

        self.image_tk = None # showing tkimage
        self.image_idx = 0 # current image idex
        self.image_cnt = 0 # num of image
        self.image_cur_id = None # showing tkimage id

        # main frame
        self.mframe = tk.Frame(self.parent)
        self.mframe.pack(fill=tk.BOTH, expand=1)

        # image frame
        self.iframe = tk.Frame(self.mframe)
        self.iframe.pack()
        self.image_canvas = tk.Canvas(self.iframe, width=self.CANVAS_WIDTH, height=self.CANVAS_HEIGHT,cursor='plus')
        self.image_canvas.pack(pady=0, anchor=tk.N)

        # control frame
        self.cframe = tk.Frame(self.mframe)
        self.cframe.pack(side=tk.TOP, padx=5, pady=10)
        self.prev_button = ttk.Button(self.cframe, text="<<", width=10, command=self.prev)
        self.prev_button.pack(side = tk.LEFT, padx=5)
        self.next_button = ttk.Button(self.cframe, text=">>", width=10, command=self.next)
        self.next_button.pack(side = tk.LEFT, padx=5)

        # status frame
        self.sframe = tk.Frame(self.mframe)
        self.sframe.pack(side=tk.TOP, padx=5, pady=10)
        self.status_label = ttk.Label(self.sframe,
                                     text="{:3d}/{:3d}".format(0,0),
                                     width=10,
                                     anchor=tk.CENTER)
        self.status_label.pack(side = tk.LEFT, padx=5)
        self.imagenum_entry = ttk.Entry(self.sframe, width=5)
        self.imagenum_entry.insert(tk.END, "")
        self.imagenum_entry.pack(side=tk.LEFT, padx=5)
        self.skip_button = ttk.Button(self.sframe, text="SKIP", width=5, command=self.skip)
        self.skip_button.pack(side=tk.LEFT, padx=5)



    def delete(self):
        # delete str in entrybox.
        self.dir_entry.delete(0, tk.END)

    def prev(self, event=None):
        if self.image_cnt == 0:
            return
        if 0 < self.image_idx:
            self.image_idx -= 1
            self.show_image(self.image_idx)

    def next(self, event=None):
        if self.image_cnt == 0:
            return
        if self.image_idx < (self.image_cnt-1):
            self.image_idx += 1
            self.show_image(self.image_idx)

    def skip(self, event=None):
        if self.image_cnt == 0:
            return
        img_num = self.imagenum_entry.get()
        if img_num.isdecimal():
            img_idx = int(img_num) - 1
            if 0 <= img_idx and img_idx <= (self.image_cnt-1):
                self.image_idx = img_idx
                self.show_image(self.image_idx)

    def update_imagestatus(self):
        if self.image_cnt != 0:
            self.status_label.configure(text="{:3d}/{:3d}".format(self.image_idx+1,self.image_cnt))
        else:
            self.status_label.configure(text="{:3d}/{:3d}".format(0,0))

    def show_image(self, idx):

        if idx < 0 or idx >= self.image_cnt:
            raise ValueError("imageidx invalid")

        # update cnavas size
        #self.image_canvas.config(width=self.CANVAS_WIDTH, height=self.CANVAS_HEIGHT)

        #-----------------------------
        # preprocess image
        #-----------------------------
        image_cv = cv2.imread(self.image_paths[idx])
        image_cv = cv2.cvtColor(image_cv, cv2.COLOR_BGR2RGB) # for PIL image

        img_height, img_width, _ = image_cv.shape
        # resize VGA
        if img_width < img_height: # portrait
            base_width = min(self.IMG_SIZE)
            base_height = max(self.IMG_SIZE)
        else: # landscape
            base_width = max(self.IMG_SIZE)
            base_height = min(self.IMG_SIZE)

        image_cv = cv2.resize(image_cv, (base_width, base_height))

        img_r, img_g, img_b = make_rgb(image_cv)
        img_y, img_u, img_v = make_yuv(image_cv)

        part_width = int(base_width/3)
        part_height = int(base_height/3)
        img_org = cv2.resize(image_cv, (part_width, part_height))
        img_dummy = np.zeros(img_org.shape, dtype=np.uint8) + 255
        img_r = cv2.resize(img_r, (part_width, part_height))
        img_g = cv2.resize(img_g, (part_width, part_height))
        img_b = cv2.resize(img_b, (part_width, part_height))
        img_y = cv2.resize(img_y, (part_width, part_height))
        img_u = cv2.resize(img_u, (part_width, part_height))
        img_v = cv2.resize(img_v, (part_width, part_height))

        image_hstack_org = np.hstack((img_dummy, img_org, img_dummy))
        image_hstack_rgb = np.hstack((img_r, img_g, img_b))
        image_hstack_yuv = np.hstack((img_y, img_u, img_v))
        disp_image = np.vstack((image_hstack_org, image_hstack_rgb, image_hstack_yuv))


        # update cnavas image
        image_pil = Image.fromarray(disp_image)
        self.image_tk = ImageTk.PhotoImage(image_pil)
        disp_x = disp_y = 0
        self.image_cur_id = self.image_canvas.create_image(disp_x, disp_y,
                                                           image=self.image_tk,
                                                           anchor=tk.NW)

        # update status label
        self.update_imagestatus()




    def open_dir(self):
        # set dirs
        self.root_dir = tkfd.askdirectory()
        self.image_dir = self.root_dir

        if self.image_dir == "":
            return

        if not os.path.exists(self.image_dir):
            tkmsg.showwarning("Warning", message="{} doesn't exist.".format(self.image_dir))
            return

        if not os.path.isdir(self.image_dir):
            tkmsg.showwarning("Warning", message="{} isn't dir.".format(self.image_dir))
            return

        self.image_paths = list()
        accepted_ext = (".jpeg", '.jpg', '.png')
        for ext in accepted_ext:
            self.image_paths.extend(glob.glob(os.path.join(self.image_dir, "*"+ext)))


        image_cnt = len(self.image_paths)
        if image_cnt == 0:
            tkmsg.showwarning("Warning", message="image doesn't exist.")
            return

        self.image_idx = 0
        self.image_cnt = image_cnt

        self.show_image(self.image_idx)


#--------------------------------------------------------
 # main
 #--------------------------------------------------------
if __name__ == '__main__':
    root = tk.Tk()
    ImageViewer(root)
    root.resizable(width=True, height=True)
    root.geometry(MAIN_DISPLAY_SIZE)
    root.mainloop()
