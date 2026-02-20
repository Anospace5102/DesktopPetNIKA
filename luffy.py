from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QPixmap   #, QMovie
from PySide6.QtWidgets import QApplication, QWidget, QLabel
import random
import os
import sys
import json

class ImageSeque():
    def __init__(self, action:str, files:list, image_time, scale=0.3):
        self.images = []
        self.image_time_MS = image_time

        if getattr(sys, 'frozen', False):
            # 打包后：exe 所在目录
            dir = os.path.dirname(sys.executable)
        else:
            # 开发时：脚本所在目录
            dir = os.path.dirname(os.path.abspath(__file__))
     
        for i in files:
            img_path=os.path.join(dir, action, i+".png") 
            img=QPixmap(img_path)
            img=img.scaled(img.size()*scale)
            self.images.append(img)   
            # print(img_path)

def get_config():
    """
    读取配置文件：
    1. 优先读取 exe 同目录的 config.json（可手动修改）
    2. 如果没有，从 exe 内置的默认配置提取
    """
    # 1. 定义路径：exe 所在目录的 config.json（外部可修改）
    if getattr(sys, 'frozen', False):
        # 打包后：exe 所在目录
        exe_dir = os.path.dirname(sys.executable)
    else:
        # 开发时：脚本所在目录
        exe_dir = os.path.dirname(os.path.abspath(__file__))
    external_config_path = os.path.join(exe_dir, "config.json")

    print("config path: "+external_config_path)
    if os.path.exists(external_config_path):
        # 读取外部可修改的配置
        with open(external_config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return {"scale":0.3, "wait":10000}
    

class DesktopPet(QWidget):
    def __init__(self, seqs:list[ImageSeque] ,* ,waiting_time=5000):
        super().__init__()
        # 动画队列类,list
        self.image_seqs = seqs #[0 ~ 8]

        # 动画组索引
        self.cur_image = 0
        self.animation_name = ["surprise     ", "go to sleep  ",
                               "waiting      ", "sleeping     ", 
                               "run right    ", "arrive right ", 
                               "run left     ", "arrive left  ", 
                               "waiting2     ", "bang         "]
        # 图片索引
        self.cur_index = 0

        # 0:常态循环，1:单次surprise
        self.mode = 0

        self.label = QLabel(self)
        self.timer = QTimer(self)

        # 单次点击标记 - 防拖拽时触发单击
        self.singleclick = False
        
        # 专门为等待进入mode 1 - sleeping的计时器
        self.timer_task_waiting = QTimer(self) 
        self.timer_task_waiting.setInterval(waiting_time )  
        self.timer_task_waiting.setSingleShot(True)  # 单次触发
        self.timer_task_waiting.timeout.connect(lambda :self.setmode(2, 1, 0))
        
        # 记录拖拉起始点
        self.drag_position = QPoint()

        print("[加载完成]")
        self.init()


    def init(self):
        # 窗口设置
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        # 设置动画标签
        self.label.setPixmap(self.image_seqs[self.cur_image].images[self.cur_index])
        self.label.resize(self.image_seqs[self.cur_image].images[self.cur_index].size())

        # 绑定timer和updateAnimation每一帧更新
        self.timer.timeout.connect(self.updateAnimation)
        self.timer.start(self.image_seqs[self.cur_image].image_time_MS) #还是得手动更新播放时间间隔(在setmode里了)
        
    
    def updateAnimation(self):
        length = len(self.image_seqs[self.cur_image].images)
        
        # 暂停模式
        if self.mode == 0:
            if self.cur_image == 5 or self.cur_image == 7 or self.cur_image == 9:
                self.setmode(1, 8, 0)
            else:
                self.setmode(1, 2, 0)

        # 循环模式
        elif self.mode == 1:
            self.cur_index = (self.cur_index + 1) % length

            # 进入waiting/waiting2 开始sleeping计时器
            if not self.timer_task_waiting.isActive() and (self.cur_image == 8 or self.cur_image == 2):
                self.timer_task_waiting.start()
                print("[timer: start        ]")
                
        # 单次模式
        elif self.mode == 2:
            self.cur_index = self.cur_index + 1

            # 播放结束
            if self.cur_index >= length:
                # 上下位置的随机波动
                ran = random.randint(50,200)
                if self.y() > 350: ran *= (-1)

                # surprise组
                if self.cur_image == 1:
                    self.setmode(1, 3, 0)

                # run_right组
                elif self.cur_image == 4:
                    print(f"({self.x()}, {self.y()}) => ({self.x()+700}, {self.y()+ran})")
                    self.move(self.x() + 750, self.y() + ran)
                    self.setmode(2, 5, 0)

                # run_left组
                elif self.cur_image == 6:
                    print(f"({self.x()}, {self.y()}) => ({self.x()-700}, {self.y()+ran})")
                    self.move(self.x() - 750, self.y() + ran)
                    self.setmode(2, 7, 0)
                    
                else:
                    self.mode = 0
                    self.cur_index = length - 1

        # # ### ########################## ### #########
        # if self.mode != 0 and self.timer_task_waiting.isActive():
        #     self.timer_task_waiting.stop()
        #     print("cancel")
        # if self.mode == 0:
        #     # self.cur_index = (self.cur_index + 1) % len(self.image_seq.images)
        #     if not self.timer_task_waiting.isActive():
        #         self.timer_task_waiting.start()
        #     print(self.timer_task_waiting.isActive())
        # elif self.mode == 1:
        #     self.cur_index = self.cur_index + 1
        #     # surprise播放完后
        #     if self.cur_index >= len(self.image_seq.images):
        #         self.mode = 0
        #         # 停回在最后一帧
        #         self.cur_index-=1
        #         self.timer_task_waiting.start()
        # elif self.mode ==2 :
        #     self.cur_index = self.cur_index + 1
        #     if self.cur_index >= len(self.image_seq.images):
        #         self.mode = 0
        #         # 停回在最后一帧
        #         self.cur_index-=1
       
        self.label.setPixmap(self.image_seqs[self.cur_image].images[self.cur_index])
        self.label.resize(self.image_seqs[self.cur_image].images[self.cur_index].size())


    # 模式设定
    def setmode(self, mode, img_seq_index, cur_img_index = 0):
        self.mode = mode
        self.cur_index = cur_img_index  # 组内图片索引
        self.cur_image = img_seq_index  # 图片组索引
        self.timer.setInterval(self.image_seqs[self.cur_image].image_time_MS)
        print("[task : "+self.animation_name[img_seq_index]+"]")

    
    # 鼠标按下
    def mousePressEvent(self, event):
        # 左键按下
        if event.button() == Qt.LeftButton:
            self.singleclick = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    # 鼠标松开
    def mouseReleaseEvent(self, event):
        # 左键  #/mode1/cur_image2,3
        if event.button() == Qt.LeftButton:# and self.mode == 1 and (self.cur_image == 2 or self.cur_image == 3):
            if self.singleclick == True:
                print("[timer: cancel       ]")
                if self.timer_task_waiting.isActive():
                    self.timer_task_waiting.stop()  #------------------------------
                self.setmode(2, 0, 0)
        elif event.button() == Qt.RightButton:
            if self.timer_task_waiting.isActive():
                self.timer_task_waiting.stop()
            self.setmode(2, 9, 0)

    # 双击事件
    def mouseDoubleClickEvent(self, event):
        self.singleclick = False
        if event.button() == Qt.LeftButton:
            if self.x() < 800:
                self.setmode(2, 4, 0)
            else:
                self.setmode(2, 6, 0)

    # 鼠标移动
    def mouseMoveEvent(self, event):
        # 左键拖动
        if event.buttons() == Qt.LeftButton:
            self.singleclick=False
            self.move(event.globalPosition().toPoint() - self.drag_position)

    # 按键检测
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            print("[ 关闭 ]")
            self.close()
            QApplication.quit()


if __name__ == "__main__":
    app=QApplication(sys.argv)

    conf = get_config()

    scale = conf["scale"]
    wait = conf["wait"]

    files1 = [f"{f_+100}" for f_ in range(1, 16)]
    surprise_imgs=ImageSeque("surprise", files1, 90, scale) 
    
    files2 = [f"{f_+200}" for f_ in range(1, 19)]   
    go_to_sleep_imgs=ImageSeque("go_to_sleep", files2, 100, scale) 

    files3 = [f"{f_+300}" for f_ in range(1, 8)]
    waiting_imgs=ImageSeque("waiting", files3, 400, scale)

    files4 = [f"{f_+400}" for f_ in range(1, 3)]
    sleeping_imgs=ImageSeque("sleeping", files4, 1500, scale)

    files5 = [f"{f_+500}" for f_ in range(1, 16)]
    run_right_imgs=ImageSeque("run_right", files5, 100, scale)

    files6 = [f"{f_+600}" for f_ in range(1, 5)]
    arrive_right_imgs=ImageSeque("arrive_right", files6, 100, scale)
    
    files7 = [f"{f_+700}" for f_ in range(1, 16)]
    run_left_imgs=ImageSeque("run_left", files7, 100, scale)

    files8 = [f"{f_+800}" for f_ in range(1, 5)]
    arrive_left_imgs=ImageSeque("arrive_left", files8, 100, scale)

    files9 = [f"{f_+900}" for f_ in range(1, 3)]
    waiting2_imgs=ImageSeque("waiting2", files9, 500, scale)

    files10 = [f"{f_+1000}" for f_ in range(1, 10)]
    bang_imgs=ImageSeque("bang", files10, 180, scale)


    luffy = DesktopPet([
        surprise_imgs, 
        go_to_sleep_imgs,
        waiting_imgs,
        sleeping_imgs,
        run_right_imgs,
        arrive_right_imgs,
        run_left_imgs,
        arrive_left_imgs,
        waiting2_imgs,
        bang_imgs
    ], waiting_time=wait)

    luffy.show()

    sys.exit(app.exec())

    