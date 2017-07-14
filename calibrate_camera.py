import cv2
import numpy as np
import glob

# Set up camera
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)

# Corners shape
nx = 9
ny = 6

objpoints = [] # 3d points in real space
imgpoints = [] # 2d points on chessboard

# Set where corners should be mapped to. (0,0,0) -- (nx-1, ny-1, 0)
mappedPoints = np.zeros((nx*ny, 3), np.float32)
mappedPoints[:, :2] = np.mgrid[0:nx, 0:ny].T.reshape(-1, 2)

# Load images
while cap.isOpened():
  ret, frame = cap.read()
  image = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
  corners_found, corners = cv2.findChessboardCorners(image, (nx, ny), None)
  cv2.drawChessboardCorners(image, (nx, ny), corners, corners_found) 
  cv2.imshow('Camera Calibration', image)
  waitKey = cv2.waitKey(1)
  if waitKey & 0xFF == ord(' '):
    if corners_found:
      print('Captured')
      objpoints.append(mappedPoints)
      imgpoints.append(corners)
    else:
      print('Could not capture corners')
  elif waitKey & 0xFF == ord('q'):
    break

cap.release()
ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, image.shape[::-1], None, None)
print(camera_matrix)
print(dist_coeffs)
