from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder

#----------------------------------------------------------------------------
import cv2,time,math
import numpy as np
from tobiiglassesctrl import TobiiGlassesController

#----------------------------------------------------------------------------
global accuracy
accuracy = 1200

#----------------------------------------------------------------------------
Conf_threshold = 0.5     # proba mini accepted
NMS_threshold = 0.4      # reduice this value de decrese the nb of box found
COLORS = [(0, 255, 0), (0, 0, 255), (255, 0, 0), (255, 255, 0), (255, 0, 255), (0, 255, 255)]

class_name = []
with open('classes.txt', 'r') as f:
    class_name = [cname.strip() for cname in f.readlines()]

net = cv2.dnn.readNet('yolov4-tiny.weights', 'yolov4-tiny.cfg')
net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA_FP16)

model = cv2.dnn_DetectionModel(net)
model.setInputParams(size=(416, 416), scale=1/255, swapRB=True)

#----------------------------------------------------------------------------
Builder.load_string('''
<WelcomeScreen>:   
    canvas.before: 
        Color: 
            rgba: (0, 0, 0,1)
        Rectangle: 
            size: root.width, root.height 
            pos: self.pos
    
    FloatLayout:
        Label:
            text :"Welcome to Tobii Glasses Application"
            color: 1, 1, 1, 1
            pos_hint: {"center_x":0.5, "center_y":0.93}
            size_hint: 0.8, 0.4
        Image:
            id: img1
            source: "tobii.jpeg"
            pos_hint: {"center_x":0.5, "center_y":0.4}
            size_hint: 0.5, 1
        Image:
            id: img2
            source: "logo_iit.png"
            pos_hint: {"center_x":0.25, "center_y":0.8}
            size_hint: 0.2, 0.2
        Image:
            id: img3
            source: "logo_tobii.jpg"
            pos_hint: {"center_x":0.75, "center_y":0.8}
            size_hint: 0.2, 0.2
        
        Button:
            id: btn1
            text: "Connection" if btn1.state == "normal" else "Connection ... "
            font_size: 30
            pos_hint: {"center_x":0.5, "center_y":0.1}
            size_hint: 0.55, 0.12 
            on_release:root.connect()

<CalibrationScreen>:   
    canvas.before: 
        Color: 
            rgba: (0, 0, 0,1)
        Rectangle: 
            size: root.width, root.height 
            pos: self.pos
    
    FloatLayout:
        Label:
            text :"Please, Watch the target !"
            color: 1, 1, 1, 1
            pos_hint: {"center_x":0.5, "center_y":0.93}
            size_hint: 0.8, 0.4
        Image:
            id: img1
            source: "target.jpeg"
            pos_hint: {"center_x":0.5, "center_y":0.65}
            size_hint: 0.5, 0.5
        Button:
            id: btn1
            text: "Start Calibration"
            font_size: 30
            pos_hint: {"center_x":0.5, "center_y":0.1}
            size_hint: 0.55, 0.12 
            on_release:root.calibration()

<VideoScreen>:   
    canvas.before: 
        Color: 
            rgba: (0, 0, 0,1)
        Rectangle: 
            size: root.width, root.height 
            pos: self.pos
    
    FloatLayout:
        Label:
            text :"Press Start to streaming"
            color: 1, 1, 1, 1
            pos_hint: {"center_x":0.5, "center_y":0.85}
            size_hint: 0.8, 0.4
        Label:
            text :"Press r on keyboard to record image"
            color: 1, 1, 1, 1
            pos_hint: {"center_x":0.5, "center_y":0.5}
            size_hint: 0.8, 0.4
        Label:
            text :"Press q on keyboard to stop"
            color: 1, 1, 1, 1
            pos_hint: {"center_x":0.5, "center_y":0.65}
            size_hint: 0.8, 0.4
        Button:
            id: btn1
            text: "Start" if btn1.state == "normal" else "Runing... "
            font_size: 30
            pos_hint: {"center_x":0.5, "center_y":0.25}
            size_hint: 0.55, 0.12 
            on_release:root.start()
        Button:
            id: btn2
            text: "Restart"
            font_size: 30
            pos_hint: {"center_x":0.5, "center_y":0.1}
            size_hint: 0.55, 0.12 
            on_release:root.restart()
''')

#----------------------------------------------------------------------------------
class TobiiApp(App):
    def build(self):
        print('Starting  Tobbi app V1')
        sm = ScreenManager()
        sm.add_widget(WelcomeScreen(name='welcomeScreen'))
        sm.add_widget(CalibrationScreen(name='calibrationScreen'))
        sm.add_widget(VideoScreen(name='videoScreen'))
        return sm

class WelcomeScreen(Screen):
    def connect(self):
        print('Trying connection with Tobii glasses')     
        global ipv4_address, tobiiglasses, project_id, participant_id
        ipv4_address = "192.168.71.50"
        tobiiglasses = TobiiGlassesController(ipv4_address, video_scene=True)
        project_id = tobiiglasses.create_project("Test live_scene_and_gaze.py")
        participant_id = tobiiglasses.create_participant(project_id, "participant_test")
        print('Connection Done')
        self.manager.current = 'calibrationScreen'

class CalibrationScreen(Screen):
    def calibration(self):
        print('Start calibration')
        global ipv4_address, tobiiglasses, project_id, participant_id, calibration_id, res
        calibration_id = tobiiglasses.create_calibration(project_id, participant_id)
        tobiiglasses.start_calibration(calibration_id)
        res = tobiiglasses.wait_until_calibration_is_done(calibration_id)

        if res is False:
            print("Calibration failed!")
            self.manager.current = 'welcomeScreen'
        else:
            print('Calibration done')
            self.manager.current = 'videoScreen'
        
class VideoScreen(Screen):
    def start(self):
        global ipv4_address, tobiiglasses, project_id, participant_id, calibration_id, res, accuracy
        stream_video(ipv4_address, tobiiglasses, project_id, participant_id, calibration_id, res, accuracy)
    def restart(self):
        self.manager.current = 'welcomeScreen'
        
#-----------------------------------------------------------------------------------------------------------------------
def stream_video(ipv4_address, tobiiglasses, project_id, participant_id, calibration_id, res, accuracy):
    print('Start Streaming')
    cap = cv2.VideoCapture("rtsp://%s:8554/live/scene" % ipv4_address)

    # Check if camera opened successfully
    if (cap.isOpened()== False):
        print("Error opening video stream or file")

    # Filtering of gaze position to know when the gaze is mouving and when is fixed
    previous_x_pos = 0
    previous_y_pos = 0

    # Read until video is completed
    tobiiglasses.start_streaming()
    i=0
    delta = 400
    first_detection = False
    x_prev_pos = 0
    y_prev_pos = 0
        
    while(cap.isOpened()):
        
        ret, frame = cap.read()
        frame = cv2.resize(frame, (1280, 720))
        
        if ret == True:
            height, width = frame.shape[:2]
            data_gp  = tobiiglasses.get_data()['gp']
            
        if data_gp['ts'] > 0:
            starting_time = time.time()
            x_pos = int(data_gp['gp'][0]*width)
            y_pos = int(data_gp['gp'][1]*height)

            # Show where the user is watching
            cv2.circle(frame,(x_pos,y_pos), 50, (0,0,255), 5)
               
        # Press r on keyboard to record one frame
        if cv2.waitKey(1) & 0xFF == ord('r'):
            detection_img = frame
            classes, scores, boxes = model.detect(detection_img, Conf_threshold, NMS_threshold)
            
            for (classid, score, box) in zip(classes, scores, boxes):
                label = "%s : %f" % (class_name[classid[0]], score)
                
                cv2.rectangle(detection_img, box, (0, 255, 255), 1)
                cv2.putText(detection_img, label, (box[0], box[1]+15), cv2.FONT_HERSHEY_COMPLEX, 0.3, (0, 255, 255), 1)
                cv2.circle(detection_img,(x_pos,y_pos), 50, (0,0,255), 5)
                
                if (box[0]<x_pos<box[2]+box[0])and (box[1]<y_pos<box[3]+box[1]):
                    object_fixed = str(label)
                    message =('last obj fixed:'+ object_fixed)
                    cv2.putText(frame, message, (50, 50), cv2.FONT_HERSHEY_COMPLEX, 0.8, (0, 255, 255), 1)
                    first_detection = True
                    
                    #saving the image
                    name_file = str(i)
                    cv2.imwrite('save_frame/' + 'image'+ str(i) + '.png', detection_img)
                    i += 1
                                
        # check velocity of the gaze acces with tobii api
        if data_gp['ts'] > 0:
            distance = math.sqrt((x_pos-x_prev_pos)**2+(x_pos-x_prev_pos)**2)
            x_prev_pos = x_pos
            y_prev_pos = y_pos
            dt = time.time() - starting_time
            velocity = int(distance/dt)
            if velocity < 500:
                # put inside the object detection
                message =('Fixation gaze')
                cv2.putText(frame, message, (700, 50), cv2.FONT_HERSHEY_COMPLEX, 0.8, (0, 255, 255), 1)
        
        # show last object fixed
        if first_detection == True:
            message =('last object fixed: '+ object_fixed)
            cv2.putText(frame, message, (50, 50), cv2.FONT_HERSHEY_COMPLEX, 0.8, (0, 255, 255), 1)
        else:
            message =('No object fixed yet')
            cv2.putText(frame, message, (50, 50), cv2.FONT_HERSHEY_COMPLEX, 0.8, (0, 255, 255), 1)
         
        # Display the resulting frame
        cv2.imshow('Tobii Pro Glasses 2 - Live Scene',frame)
        
        # Press q on keyboard to  exit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # When everything done, release the video capture object
    cap.release()
    # Closes all the frames
    cv2.destroyAllWindows()
    # Disconnect tobbiglasses
    tobiiglasses.stop_streaming()
    tobiiglasses.close()

#---------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    TobiiApp().run()