import cv2
import numpy as np
import math


def stream(ipv4_address, tobiiglasses, project_id, participant_id, calibration_id, res, accuracy):
    print('inside stream')
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
    delta = 100
    just_record = False
    
    while(cap.isOpened()):

        ret, frame = cap.read()
        if ret == True:
            height, width = frame.shape[:2]
            data_gp  = tobiiglasses.get_data()['gp']
            
        if data_gp['ts'] > 0:
            x_pos = int(data_gp['gp'][0]*width)
            y_pos = int(data_gp['gp'][1]*height)
            distance = math.sqrt((abs(previous_x_pos - x_pos)**2) + (abs(previous_x_pos - x_pos)**2))
            #print('distance', int(distance))
            font = cv2.FONT_HERSHEY_SIMPLEX 
            
            '''
            if distance < accuracy:
                cv2.putText(frame, 'GAZE FIXED', (50,50),font,1,(0,255,255),2,cv2.LINE_4)
                x_pos = previous_x_pos
                y_pos = previous_y_pos
            else:
                cv2.putText(frame, 'GAZE MOUVING', (50,50),font,1,(0,255,255),2,cv2.LINE_4)
            '''
            
            # Show where the user is watching
            cv2.circle(frame,(x_pos,y_pos), 50, (0,0,255), 5)

        # Display the resulting frame
        cv2.imshow('Tobii Pro Glasses 2 - Live Scene',frame)

        # Press r on keyboard to record one frame
        if cv2.waitKey(1) & 0xFF == ord('r'):
            cropped_image = frame[x_pos-delta:x_pos+delta, y_pos-delta:y_pos+delta]
            cv2.imwrite('save_frame/Frame'+str(i)+'.jpg', cropped_image)
            i += 1
            just_record = True
            
        # Press q on keyboard to exit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


    # When everything done, release the video capture object
    cap.release()
    # Closes all the frames
    cv2.destroyAllWindows()

    # Disconnect tobbiglasses
    tobiiglasses.stop_streaming()
    tobiiglasses.close()


