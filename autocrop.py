import cv2
from matplotlib import pyplot as plt
import numpy as np
import os,re,shutil

# http://matplotlib.org/users/whats_new.html#html5-canvas-backend
# seems to have interactive ability as well
def hull_method(gray):
    ret,thresh = cv2.threshold(gray,127,255,0)
    contours,hier = cv2.findContours(thresh,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)
    
    squares = []
    for cnt in contours:
        if cv2.contourArea(cnt)>5000:
            hull = cv2.convexHull(cnt)
            hull = cv2.approxPolyDP(hull,0.1*cv2.arcLength(hull,True),True)
            if len(hull)==4:
                squares.append(hull)
    return squares
    
def pick_best_square(squares):
    biggest_area = -1
    index = 0
    for square in squares:
        if cv2.contourArea(square) > biggest_area:
            biggest_area = cv2.contourArea(square)
            biggest_square = index
        index = index + 1
    return biggest_square
    
def transform_square(img, squares):
    global current_square
    square = squares[current_square]
    if current_square==-1:
        square = squares[pick_best_square(squares)]
    A4Width = 2480
    A4Height = 3508
    src = np.array(square, np.float32)
    dst = np.array([[0,0],[A4Width,0],[A4Width,A4Height],[0,A4Height]], np.float32)
    tf = cv2.getPerspectiveTransform(src,dst)
    warp = cv2.warpPerspective(img,tf,(A4Width,A4Height))
    return warp

def load_next_frame(files):
    global current_file, img_to_transform, squares
    try:
        got_file = False
        while not got_file:
            current_file = files.pop()
            m = re.match(".*(jpg|jpeg)$", current_file)
            if m:
                got_file = True
        print current_file
        img_to_transform = cv2.imread(home_folder + "/" + current_file)
        imgray = cv2.cvtColor(img_to_transform, cv2.COLOR_BGR2GRAY)
        squares = hull_method(imgray)
        transform()
        redraw()
    except Exception, e:
        print e

def transform():
    global axes, img_to_transform, squares
    transformed = transform_square(img_to_transform, squares)
    axes[1].imshow(transformed)
    return transformed
    
def redraw():
    global axes, img_to_transform, squares, current_square, fig, draw_corner
    annotated_image = img_to_transform.copy()
    cv2.circle(annotated_image, tuple(squares[current_square][draw_corner][0]), radius=35, color=(255,0,0), thickness=10)
    cv2.drawContours(annotated_image, squares, -1, (0, 255, 0), 3 )
    cv2.drawContours(annotated_image, [squares[current_square]], -1, (255, 0, 0), 3)
    axes[0].imshow(annotated_image)
    fig.canvas.draw()    
    
def press(event):
    global current_file, files, draw_corner, current_square, fig
#    print('press', event.key)
#    sys.stdout.flush()
    if event.key==' ':
        current_square = -1
        load_next_frame(files)
    # FIXME this could get complicated, direct o to p breaks system?
    if event.key=='o' or event.key=='p': # event.key=='d'
#        fig.text(0.01,0.01,"draw_corner %d" % draw_corner,fontsize=10)
        print "draw_corner %d" % draw_corner
        if draw_corner >= 0:
            draw_corner = -1
        else:
            draw_corner = 0
    if event.key=='w':
        transformed = transform()
        cv2.imwrite(home_folder + "/transformed/" + current_file, transformed)
        shutil.move(home_folder + "/" + current_file, home_folder + "/original/" + current_file)
        print "saved %s" % current_file
        current_square = -1
        load_next_frame(files)
    if event.key=='~': # s is mpl save
        current_square = current_square + 1
        if current_square >= len(squares):
            current_square = -1
        transform()
        redraw()
    if event.key=='!':
        # cycles clockwize from a random corner
        draw_corner = (draw_corner + 1) % 4
        redraw()
        
def onclick(event):
    global draw_corner, squares, current_square
    if draw_corner >= 0 and event.button==1:
        # TODO check if within the image border
        squares[current_square][draw_corner] = [int(event.xdata), int(event.ydata)]
        transform()
        redraw()

# globals    
transformed = None
draw_corner = 0
img_to_transform = None
current_file = None
current_square = -1
squares = None

# config
# home_folder = "c:/share/camera_scan"
home_folder = "T:/home/data/camera_scan/discovery"
files = os.listdir(home_folder)
fig, axes = plt.subplots(1,2)
axes[0].set_title("Original Image")
axes[1].set_title("Cropped Image")
fig.text(0.01,0.99,"""
space  get next image, ~      change rectangle, !      change corner
""",fontsize=10)

fig.canvas.mpl_connect('key_press_event', press)
fig.canvas.mpl_connect('button_press_event', onclick)
load_next_frame(files)
