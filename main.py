import tkinter as tk
import tkinter.messagebox
from tkinterdnd2 import *
import tkinter.filedialog
from PIL import Image, ImageTk, ImageFile
import os
import configparser
import glob
import random
import re

class Application(tk.Frame):
    global picture
    def __init__(self, master = None):
        super().__init__(master)
        ImageFile.LOAD_TRUNCATED_IMAGES = True
        self.config = configparser.ConfigParser()
        self.set_path = os.path.join(os.path.dirname(__file__), 'setting.ini')
        self.config.read(self.set_path,"UTF-8")
        self.fullsc = False
        self.master.title('ImageViewer')
        self.master.geometry(self.config["SETTING"]["geometry"])
        self.back_color = "#000000"
        
        self.pil_image = None # 画像ファイル
        self.menu() # メニューの生成
        self.widget() # ウィジェットの生成
        
        self.master.protocol("WM_DELETE_WINDOW", self.close_window) # バツボタンを押した時の処理

    def widget(self):
        self.canvas = tk.Canvas(self.master, background= self.back_color, bd=-2)
        self.canvas.pack(expand=True,  fill="both")
        icon_path = os.path.join(os.path.dirname(__file__), "icon.ico")
        self.master.iconbitmap(default=icon_path)

        fullsc = self.config["SETTING"]["fullsc"] # フルスクリーンフラグ
        
        if fullsc == "True":
            self.fullscreen()

        self.master.bind('<Double-1>', self.fullscreen) # ダブルクリックでフルスクリーン
        self.master.bind("<Button-1>", self.mouse_click) # クリック時の処理
        self.master.bind("<B1-Motion>", self.mouse_drag) # マウスドラッグ処理
        self.master.bind("<Control-MouseWheel>", self.turn)
        self.master.bind("<MouseWheel>", self.mouse_wheel) # マウスホイール時の処理
        self.master.bind("<Button-2>", self.close_window) # マウス中ボタンで終了
        self.master.bind("<Motion>", self.mouse_move) # マウス移動検出
        self.master.bind("<Button-3>", self.mouse_right) # 右クリック処理
        self.master.bind("<Left>", self.leftkey) # 左矢印キー処理
        self.master.bind("<Right>", self.rightkey) # 右矢印キー処理

        self.master.dnd_bind("<<Drop>>", self.get_drop) # ドラッグドロップ処理

        # 右クリックメニューの設定
        self.click_menu = tk.Menu(self.master, tearoff=0)
        self.click_menu.add_command(label="画像をウィンドウに合わせる", command=self.windowsize)
        self.click_menu.add_command(label="ファイルを開く", command=self.open_file)
        self.click_menu.add_command(label="全画面切り替え", command=self.fullscreen)

    # クリック位置の取得
    def mouse_click(self, event):
        if self.pil_image == None:
            return
        self.click_event = event # クリック位置

    # ドラッグで画像を動かす
    def mouse_drag(self, event):
        if self.pil_image == None:
            return

        pic_place = self.canvas.coords("pic") # 画像の現在位置を取得
        self.place_width = event.x - self.click_event.x + pic_place[0]
        self.place_height = event.y - self.click_event.y + pic_place[1]
        self.canvas.coords("pic", self.place_width, self.place_height) # 画像を平行移動

        self.click_event = event
    
    # マウスホイールで拡大縮小
    def mouse_wheel(self, event):
        if self.pil_image == None:
            return

        pic_place = self.canvas.coords("pic") # 画像の現在位置を取得

        if event.delta > 0:
            self.minscale = False
            self.scale_point = self.scale_point * 1.25 * self.scale_rate
        else:
            if self.minscale:
                return
            self.scale_point = self.scale_point * 0.8 * (1/self.scale_rate)

        self.resize_width = int(self.default_width * self.scale_point)
        self.resize_height = int(self.default_height * self.scale_point)

        if self.resize_width <= 10 or self.resize_height <= 10:
            self.minscale = True
            return
        
        # キャンバスの初期化
        self.canvas.delete("all")

        self.pil_image = self.original.resize((self.resize_width, self.resize_height))
        self.pil_image = self.pil_image.rotate(self.degree_point, expand=True)
        self.photo_image = ImageTk.PhotoImage(self.pil_image)
        self.canvas.create_image(pic_place[0], pic_place[1], image=self.photo_image, tag="pic")

    # マウスの座標を取得
    def mouse_move(self, event):
        if self.pil_image == None:
            return
        self.mouse_point = event
    
    # 右クリックでメニューを開く
    def mouse_right(self, event):
        self.click_menu.post(event.x_root, event.y_root)
    
    # 画像を回転させる
    def turn(self, event):
        if self.pil_image == None:
            return

        pic_place = self.canvas.coords("pic")

        # キャンバスの初期化
        self.canvas.delete("all")

        turn_degree = event.delta / 120 * self.rotate_rate
        self.degree_point = int(turn_degree + self.degree_point)
        self.pil_image = self.original.resize((self.resize_width,self.resize_height))
        self.pil_image = self.pil_image.rotate(self.degree_point, expand=True)
        self.photo_image = ImageTk.PhotoImage(self.pil_image)

        self.canvas.create_image(pic_place[0], pic_place[1], image=self.photo_image, tag="pic")
    
    # 左矢印キーの処理
    def leftkey(self, event=None):
        if self.pil_image == None:
            return
        index = self.random_data.index(self.file_path)
        if index == 0:
            self.random_data = random.sample(self.filenames, len(self.filenames))
            index = self.random_data.index(self.file_path)
            self.random_data[-1], self.random_data[index] = self.random_data[index], self.random_data[-1]

        self.file_path = self.random_data[index-1]
        self.set_image(self.file_path)

    # 右矢印キーの処理
    def rightkey(self, event=None):
        if self.pil_image == None:
            return
        index = self.random_data.index(self.file_path)
        if index == len(self.random_data)-1:
            self.random_data = random.sample(self.filenames, len(self.filenames))
            index = self.random_data.index(self.file_path)
            self.random_data[0], self.random_data[index] = self.random_data[index], self.random_data[0]

        self.file_path = self.random_data[index+1]
        self.set_image(self.file_path)

    # ウィンドウのサイズに画像を合わせる
    def windowsize(self):
        if self.pil_image == None:
            return
        height_rate = self.original.height / self.original.width
        self.image_fit(self.pil_image.width, self.pil_image.width * height_rate) # 画像をウインドウに合わせる
        self.draw_image(self.pil_image)

    # フォルダーから画像を開く
    def open_file(self):

        self.file_path = tkinter.filedialog.askopenfilename(filetypes= [('Image file', '.bmp .png .jpg .jpeg .bmp .gif .webp')])
        self.set_image(self.file_path)
        self.get_parent()

    # ドロップされたファイルを取得
    def get_drop(self, event):
        self.file_path = event.data

        # パスの文字列が{}で括られてしまう場合があり（仕様？），それを取り除く処理
        if self.file_path[0] == "{":
            self.file_path = self.file_path[1:-1]
        
        if "\\" in self.file_path:
            self.file_path = re.sub(r"\\", "/", self.file_path)

        if not (".bmp" in self.file_path.casefold() or ".png" in self.file_path.casefold() or ".jpg" in self.file_path.casefold() or ".jpeg" in self.file_path.casefold() or ".bmp" in self.file_path.casefold() or ".gif" in self.file_path.casefold() or ".webp" in self.file_path.casefold()):
            return   

        self.set_image(self.file_path)
        self.get_parent()

    def set_image(self, file_path):
        if not file_path:
            return
        # キャンバスの初期化
        self.canvas.delete("all")
        self.pil_image = Image.open(file_path) # 表示用の画像データ
        self.original = Image.open(file_path) # 元の画像を保持

        # JPEGの回転情報の反映
        try:
            exifinfo = self.original._getexif()
            orientation = exifinfo.get(0x112, 1)
            if orientation == 2:
                img_rotate = self.original.transpose(Image.FLIP_LEFT_RIGHT)
            elif orientation == 3:
                img_rotate = self.original.transpose(Image.ROTATE_180)
            elif orientation == 4:
                img_rotate = self.original.transpose(Image.FLIP_TOP_BOTTOM)
            elif orientation == 5:
                img_rotate = self.original.transpose(Image.FLIP_LEFT_RIGHT).transpose(Image.ROTATE_90)
            elif orientation == 6:
                img_rotate = self.original.transpose(Image.ROTATE_270)
            elif orientation == 7:                
                img_rotate = self.original.transpose(Image.FLIP_LEFT_RIGHT).transpose(Image.ROTATE_270)
            elif orientation == 8:
                img_rotate = self.original.transpose(Image.ROTATE_90)
            else:
                pass
            self.pil_image = img_rotate
            self.original = img_rotate
        except:
            pass
        self.image_fit(self.pil_image.width, self.pil_image.height) # 画像をウインドウに合わせる
        self.draw_image(self.pil_image)

    # 画像をウィンドウに合わせる
    def image_fit(self, image_width, image_height):

        # キャンバスサイズの取得
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        # 拡大率
        width_rate =  canvas_width / image_width
        height_rate = canvas_height / image_height

        if width_rate >= height_rate:
            self.pil_image = self.original.resize((int(image_width*height_rate),canvas_height))
        else:
            self.pil_image = self.original.resize((canvas_width,int(image_height*width_rate)))

    # 画像を描画
    def draw_image(self, pil_image):
        
        if pil_image == None:
            return
        
        # キャンバスの初期化
        self.canvas.delete("all")

        # キャンバスサイズの取得
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        # 初期値設定
        self.photo_image = ImageTk.PhotoImage(self.pil_image)
        self.move_x = 0
        self.move_y = 0
        self.place_width = 0
        self.place_height = 0
        self.default_width = self.pil_image.width
        self.default_height = self.pil_image.height
        self.resize_width = self.default_width
        self.resize_height = self.default_height
        self.scale_rate = 0.8 + (int(self.config["SETTING"]["scale_rate"]) / 10)
        self.scale_point = 1
        self.rotate_rate = int(self.config["SETTING"]["rotate_rate"])
        self.degree_point = 0
        self.minscale = False

        # 画像を表示
        self.canvas.create_image(canvas_width/2, canvas_height/2, image=self.photo_image, tag="pic")

    # フォルダ内ファイルを取得してランダムに並べ替える    
    def get_parent(self):
        if self.pil_image == None:
            return
        self.parent_path = os.path.dirname(self.file_path) # 親ディレクトリを取得
        types = (".bmp", ".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp")
        self.filenames = []
        for i in types:
            parent_file = self.parent_path + "/*" + i
            self.filenames += glob.glob(parent_file)
        self.filenames = [self.filenames[i].replace("\\", "/") for i in range(len(self.filenames))]
        self.random_data = random.sample(self.filenames, len(self.filenames))
        index = self.random_data.index(self.file_path)
        self.random_data[0], self.random_data[index] = self.random_data[index], self.random_data[0]
    
    # 終了
    def close_window(self, event=None):
        if not self.fullsc:
            self.config["SETTING"]["geometry"] = str(self.master.geometry())
        with open(self.set_path, "w") as file:
            self.config.write(file)
        self.master.destroy()
        return

    # メニューバー
    def menu(self):
        menubar = tk.Menu(self)
        self.menubar = menubar
        self.master.config(menu=menubar, relief=tk.FLAT, borderwidth=-10)
        menubutton = tk.Menu(menubar, tearoff=0, relief=tk.FLAT, borderwidth=-10)
        menubar.add_cascade(label="メニュー", menu=menubutton)
        menubutton.add_command(label="新規ウィンドウ", command=self.new_window)
        menubutton.add_command(label="ファイルを開く", command=self.open_file)
        menubutton.add_command(label="終了", command=self.close_window)

    # フルスクリーン変更
    def fullscreen(self, event=None):
        
        self.fullsc = not self.fullsc # フルスクリーンフラグの更新
        self.config["SETTING"]["fullsc"] = str(self.fullsc)
        if self.fullsc:
            self.menubar.destroy()
            self.config["SETTING"]["geometry"] = str(self.master.geometry())
        else:
            self.menu()
        self.master.attributes('-fullscreen', self.fullsc)
        if self.pil_image != None:
            self.canvas.update()
            height_rate = self.original.height / self.original.width
            self.image_fit(self.pil_image.width, self.pil_image.width * height_rate)
            self.draw_image(self.pil_image)
        
    
    # 新規ウィンドウを開く
    def new_window(self):
        file = open(__file__, encoding='UTF-8')
        exec(file.read())

if __name__ == '__main__':
    disp = TkinterDnD.Tk()
    disp.drop_target_register(DND_FILES)
    app = Application(master = disp)
    app.mainloop()
