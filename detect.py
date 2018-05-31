import Vehicle
from cartesian import distance
import numpy as np
import cv2
import sys
import time

VIDEO_SOURCE = sys.argv[1]
MIN_AREA = 500

'''
def on_mouse(event, x, y, buttons, user_param):
    if event == cv2.EVENT_LBUTTONDOWN:
        polygon.append([x, y])
'''   

def detectVehicle(stats, centroids, frame, frame_id, buffer_frames, vehicles, road_points):
    points = list()
    for i in range(len(stats)):
        stat = stats[i]
        area = stat[cv2.CC_STAT_AREA]
        centroid = (int(centroids[i][0]), int(centroids[i][1]))

        if (area >= MIN_AREA) and inSquare(road_points, centroid, 'bottom-up'):
            if not vehicles:
                vehicles.append(Vehicle.Vehicle(len(vehicles), frame_id, centroid, stat))
            else:
                points.append([centroid, stat])
            
    if buffer_frames:
        vehicles = findVehicles(vehicles, buffer_frames[0], frame_id, 30)
    print(points)
    if points:
        buffer_frames = addFrame(points, buffer_frames, 1)
    return buffer_frames, frame

def inSquare(road_area, point, way):
    high_y = road_area[1][1]
    low_y = road_area[0][1]
    high_x = int((road_area[2][0]+road_area[3][0])/2) + 5
    low_x = int((road_area[0][0]+road_area[1][0])/2) - 5
    if way == 'bottom-up':
        in_y = point[1] < high_y and point[1] > low_y
        in_x = point[0] < high_x and point[0] > low_x
        if in_x and in_y:
            return True
        else:
            return False

def findVehicles(vehicles, points, frame_id, max_distance=40):
    for vehicle in vehicles:
        found = False
        for point in points:
            if distance(vehicle.getCurrentPose(), point[0]) <= max_distance:
                vehicle.setCurrentPose(point[0], point[1], frame_id)
                points.remove(point)
                found = True
                break
        if not found:
            vehicle.incrementNoFrame()
    if points:
        for point in points:
            vehicles.append(Vehicle.Vehicle(len(vehicles), frame_id, point[0], point[1]))
    return vehicles

def addFrame(frame, buffer, max_size=10):
    if len(buffer) >= max_size:
        buffer.pop()
    buffer.insert(0, frame)
    return buffer


#def inCars(centroid):

def main():
    vehicles = list()
    buffer_frames = list()

    capture = cv2.VideoCapture(VIDEO_SOURCE)
    backsub = cv2.bgsegm.createBackgroundSubtractorMOG()

    #cv2.setMouseCallback("Draw Polygon", on_mouse)

    road_points = [[90,180], [5,244], [202,244], [214,180]]     #video.mp4
    road_area = np.array(road_points, np.int32)
    road_area = road_area.reshape((-1,1,2))

    cv2.namedWindow('Background')
    cv2.moveWindow('Background', 400, 0)
    cv2.namedWindow('Track')

    while capture.isOpened():
        frame_id = int(capture.get(1))
        ret, frame = capture.read()
        
        bkframe = backsub.apply(frame, None, 0.01)
        bkframe = cv2.medianBlur(bkframe, 7)
        bkframe = cv2.blur(bkframe, (7,7))

        num, labels, stats, centroids = cv2.connectedComponentsWithStats(bkframe, ltype=cv2.CV_16U)

        buffer_frames, frame = detectVehicle(stats, centroids, frame, frame_id, buffer_frames, vehicles, road_points)
        for vehicle in vehicles:
            if not vehicle.isHide():
                vehicle.show()
                vehicle.drawVehicle(frame)
                vehicle.drawTrack(frame)

        cv2.polylines(frame, [road_area], True, (0,255,0), 3)
        #cv2.putText(frame,'COUNT: %r' %vehicle_counter, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

        cv2.imshow('Track', frame)
        cv2.imshow('Background', bkframe)
        time.sleep(0.5)

        if cv2.waitKey(100) == ord('q'):
                break


if __name__ == '__main__':
    main()