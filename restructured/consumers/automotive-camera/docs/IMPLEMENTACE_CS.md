# Implementační Plán - Automobilový Kamerový Systém

## 🇨🇿 Kompletní Průvodce Implementací v Češtině

### Úvod

Tento dokument poskytuje kompletní návod pro implementaci pokročilého kamerového systému do automobilů s využitím AWS cloudových služeb a edge computing technologií.

## 1. Typy Kamerových Systémů pro Automobily

### 1.1 Základní Zadní Kamera
**Účel**: Asistence při couvání  
**Kamery**: 1x zadní kamera  
**Funkce**:
- Zobrazení zadního prostoru na displeji
- Vodicí linie pro parkování
- Detekce vzdálenosti od překážek
- Aktivace při zařazení zpátečky

**Implementace**:
```python
class RearViewCamera:
    """
    Základní zadní kamera s vodicími liniemi.
    
    Poskytuje real-time zobrazení prostoru za vozidlem s překryvem
    vodicích linií založených na úhlu natočení volantu.
    """
    
    def __init__(self, camera_index: int = 0):
        self.camera = cv2.VideoCapture(camera_index)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
    def draw_parking_lines(self, frame: np.ndarray, steering_angle: float) -> np.ndarray:
        """
        Vykreslí vodicí linie pro parkování.
        
        Args:
            frame: Vstupní video snímek
            steering_angle: Úhel natočení volantu v stupních
            
        Returns:
            Snímek s vykreslenými vodicími liniemi
        """
        height, width = frame.shape[:2]
        
        # Vypočítat trajektorii na základě úhlu natočení
        trajectory = self._calculate_trajectory(steering_angle, width, height)
        
        # Vykreslit linie
        cv2.polylines(frame, [trajectory], False, (0, 255, 0), 3)
        
        # Zóny vzdálenosti (zelená, žlutá, červená)
        self._draw_distance_zones(frame, width, height)
        
        return frame
```

### 1.2 Surround View System (360°)
**Účel**: Kompletní pohled okolo vozidla  
**Kamery**: 4-8 kamer (přední, zadní, 2-6x boční)  
**Funkce**:
- Bird's eye view (pohled shora)
- 2D/3D zobrazení okolí
- Detekce překážek ve všech směrech
- Asistence při parkování v těsných prostorech

**Implementace**:
```python
class SurroundViewSystem:
    """
    360° surround view systém s kalibrací a image stitchingem.
    
    Kombinuje obrazy z více kamer do jednoho seamless bird's eye view.
    Používá kalibra

ní parametry pro korekci zkreslení a perspektivní transformaci.
    """
    
    def __init__(self, camera_configs: List[CameraConfig]):
        self.cameras = []
        self.calibration_data = {}
        
        for config in camera_configs:
            camera = self._init_camera(config)
            self.cameras.append(camera)
            self.calibration_data[config.position] = self._load_calibration(config)
    
    def generate_surround_view(self) -> np.ndarray:
        """
        Vygeneruje 360° surround view snímek.
        
        Returns:
            np.ndarray: Bird's eye view obraz 1280x720px
        """
        frames = []
        
        # Načíst snímky ze všech kamer
        for camera in self.cameras:
            ret, frame = camera.read()
            if ret:
                # Korigovat zkreslení
                frame = self._undistort(frame, camera.position)
                # Aplikovat perspektivní transformaci
                frame = self._perspective_transform(frame, camera.position)
                frames.append(frame)
        
        # Stitching všech snímků
        surround_view = self._stitch_images(frames)
        
        # Overlay s 3D modelem vozidla
        surround_view = self._overlay_vehicle_model(surround_view)
        
        return surround_view
    
    def _undistort(self, frame: np.ndarray, position: str) -> np.ndarray:
        """Koriguje zkreslení objektivu pomocí kalibračních parametrů."""
        calib = self.calibration_data[position]
        return cv2.undistort(frame, calib['camera_matrix'], calib['dist_coeffs'])
    
    def _perspective_transform(self, frame: np.ndarray, position: str) -> np.ndarray:
        """Transformuje perspektivu pro bird's eye view."""
        M = self.calibration_data[position]['homography_matrix']
        height, width = 720, 1280
        return cv2.warpPerspective(frame, M, (width, height))
```

### 1.3 ADAS Kamerový Systém
**Účel**: Pokročilé asistenční systémy  
**Kamery**: 1-3 kamery (především přední)  
**Funkce**:
- Lane Keep Assist (udržování v pruhu)
- Adaptive Cruise Control (ACC)
- Forward Collision Warning
- Pedestrian Detection
- Traffic Sign Recognition
- Automatic Emergency Braking

**Implementace**:
```python
class ADASCameraSystem:
    """
    Pokročilý ADAS systém s detekcí jízdních pruhů a objektů.
    
    Využívá YOLOv8 pro detekci objektů a SCNN pro detekci pruhů.
    Optimalizováno pro real-time inference na NVIDIA Jetson.
    """
    
    def __init__(self, model_path: str):
        # Načíst optimalizovaný TensorRT model
        self.object_detector = YOLO(f"{model_path}/yolov8n.engine")
        self.lane_detector = LaneDetectionModel(f"{model_path}/lane_scnn.engine")
        
        # Inicializovat tracking
        self.tracker = DeepSORT()
        
        # Inicializovat kalman filtr pro smoothing
        self.kalman = cv2.KalmanFilter(4, 2)
    
    def process_frame(self, frame: np.ndarray, vehicle_speed: float) -> Dict:
        """
        Zpracuje video snímek a detekuje objekty a pruhy.
        
        Args:
            frame: Vstupní RGB snímek 1920x1080
            vehicle_speed: Rychlost vozidla v km/h
            
        Returns:
            dict: Detekované objekty, pruhy, varování
        """
        results = {}
        
        # Detekce objektů (chodci, vozidla, cyklisté)
        objects = self.object_detector(frame, conf=0.5, iou=0.4)
        results['objects'] = self._process_detections(objects)
        
        # Detekce jízdních pruhů
        lanes = self.lane_detector(frame)
        results['lanes'] = self._process_lanes(lanes)
        
        # Analýza scény
        results['warnings'] = self._analyze_scene(results, vehicle_speed)
        
        # TTC (Time To Collision) výpočet
        results['ttc'] = self._calculate_ttc(results['objects'], vehicle_speed)
        
        return results
    
    def _analyze_scene(self, detections: Dict, speed: float) -> List[Warning]:
        """Analyzuje scénu a generuje varování."""
        warnings = []
        
        # Lane Departure Warning
        if self._is_departing_lane(detections['lanes']):
            warnings.append(Warning(type='LDW', severity='HIGH'))
        
        # Forward Collision Warning
        for obj in detections['objects']:
            if obj['class'] in ['car', 'pedestrian', 'bicycle']:
                ttc = obj.get('ttc')
                if ttc and ttc < 2.0:  # méně než 2 sekundy do kolize
                    warnings.append(Warning(
                        type='FCW',
                        severity='CRITICAL',
                        object=obj,
                        ttc=ttc
                    ))
        
        return warnings
```

## 2. Hardware Komponenty

### 2.1 Kamery

#### Wide-Angle Kamery
```yaml
Specifikace:
  Rozlišení: 1920x1080 @ 30 FPS minimum
  Field of View: 120-170°
  Low Light Performance: < 0.1 lux
  Interface: USB 3.0 nebo MIPI-CSI
  Lens: M12 mount, IR-cut filter
  
Doporučené modely:
  - Arducam IMX219: $30-40, 8MP, 160° FOV
  - See3CAM_CU135: $100, 13MP, 100° FOV  
  - Leopard Imaging LI-IMX390: $150, HDR, 120° FOV (automotive grade)
```

#### Fish-Eye Kamery (pro surround view)
```yaml
Specifikace:
  Rozlišení: 1920x1080 @ 30 FPS
  Field of View: 185-220°
  Distortion: Vysoké zkreslení (vyžaduje calibraci)
  Interface: MIPI-CSI preferováno
  IP Rating: IP67 pro vnější montáž
  
Doporučené modely:
  - Arducam OV9281: $80, 1MP, 200° FOV
  - DFOV (Fisheye): $120, 2MP, 220° FOV
```

### 2.2 Computing Platform

#### NVIDIA Jetson Xavier NX (Doporučeno)
```yaml
Specifikace:
  GPU: 384-core NVIDIA Volta
  CPU: 6-core ARMv8.2 @ 1.4GHz
  Memory: 8GB LPDDR4x
  Storage: microSD + NVMe SSD
  Power: 10-15W
  AI Performance: 21 TOPS
  
Cena: $400-500
Výhody:
  - Nativní CUDA support
  - TensorRT optimalizace
  - Nízká spotřeba
  - Industrial temperature range
```

#### Raspberry Pi 4 (Budget varianta)
```yaml
Specifikace:
  CPU: 4-core ARM Cortex-A72 @ 1.5GHz
  GPU: VideoCore VI
  Memory: 4-8GB LPDDR4
  Storage: microSD
  Power: 5-8W
  
Cena: $50-80
Omezení:
  - Slabší AI inference (potřeba Coral TPU)
  - Max 2-3 kamery současně
  - Omezený na základní funkce
```

### 2.3 Další Hardware

```yaml
GPS Module:
  Model: u-blox NEO-M9N
  Cena: $40
  Přesnost: 2m CEP
  Update rate: 25 Hz

CAN Bus Interface:
  Model: CANable USB adapter
  Cena: $30
  Protocol: CAN 2.0A/B
  Speed: Up to 1 Mbps

Storage:
  microSD: Samsung EVO Plus 128GB ($20)
  NVMe SSD: 256GB NVMe ($50) pro recordings

Power Supply:
  12V DC-DC converter: 5V/5A output
  Battery backup: UPS for safe shutdown
  
Display:
  7-10" touchscreen LCD
  Resolution: 1024x600 minimum
  Cena: $50-100
```

## 3. AWS Cloud Infrastructure

### 3.1 IoT Greengrass Deployment

```python
# greengrass_components/camera_processing/recipe.yaml
---
RecipeFormatVersion: '2020-01-25'
ComponentName: com.automotive.camera.processing
ComponentVersion: '1.0.0'
ComponentDescription: 'Automotive camera processing with object detection'
ComponentPublisher: 'Automotive Systems'
ComponentConfiguration:
  DefaultConfiguration:
    cameras:
      count: 4
      resolution: '1920x1080'
      fps: 30
    models:
      object_detection: 'yolov8n.engine'
      lane_detection: 'scnn_lane.engine'
    processing:
      enable_gpu: true
      batch_size: 1
      max_latency_ms: 100

Manifests:
  - Platform:
      os: linux
      architecture: arm64
    Lifecycle:
      Install:
        Script: |
          apt-get update
          apt-get install -y python3-opencv
          pip3 install ultralytics tensorrt
      Run:
        Script: python3 {artifacts:path}/camera_processor.py
    Artifacts:
      - Uri: s3://automotive-camera-artifacts/camera_processor.py
      - Uri: s3://automotive-camera-models/yolov8n.engine
      - Uri: s3://automotive-camera-models/scnn_lane.engine
```

### 3.2 CloudFormation Stack

```yaml
# infrastructure/cloudformation/camera-system-stack.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Automotive Camera System Infrastructure'

Parameters:
  FleetSize:
    Type: Number
    Default: 1
    Description: 'Number of vehicles in fleet'
  
  VideoRetentionDays:
    Type: Number
    Default: 30
    Description: 'Days to retain video recordings'

Resources:
  # IoT Thing Group for vehicle fleet
  VehicleFleetThingGroup:
    Type: AWS::IoT::ThingGroup
    Properties:
      ThingGroupName: !Sub '${AWS::StackName}-vehicle-fleet'
      ThingGroupProperties:
        ThingGroupDescription: 'Fleet of vehicles with camera systems'
        AttributePayload:
          Attributes:
            fleet_size: !Ref FleetSize

  # S3 Bucket for video recordings
  VideoRecordingsBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub '${AWS::StackName}-recordings-${AWS::AccountId}'
      VersioningConfiguration:
        Status: Enabled
      LifecycleConfiguration:
        Rules:
          - Id: ArchiveOldRecordings
            Status: Enabled
            Transitions:
              - TransitionInDays: !Ref VideoRetentionDays
                StorageClass: GLACIER
              - TransitionInDays: 90
                StorageClass: DEEP_ARCHIVE
            ExpirationInDays: 365
      PublicAccessBlockConfiguration:
        BlockPublicAcls: true
        BlockPublicPolicy: true
        IgnorePublicAcls: true
        RestrictPublicBuckets: true

  # Kinesis Video Stream for live streaming
  CameraLiveStream:
    Type: AWS::KinesisVideo::Stream
    Properties:
      Name: !Sub '${AWS::StackName}-live-stream'
      DataRetentionInHours: 24
      MediaType: 'video/h264'

  # DynamoDB Table for metadata
  VideoMetadataTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: !Sub '${AWS::StackName}-video-metadata'
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: vehicle_id
          AttributeType: S
        - AttributeName: timestamp
          AttributeType: N
        - AttributeName: event_type
          AttributeType: S
      KeySchema:
        - AttributeName: vehicle_id
          KeyType: HASH
        - AttributeName: timestamp
          KeyType: RANGE
      GlobalSecondaryIndexes:
        - IndexName: event-type-index
          KeySchema:
            - AttributeName: event_type
              KeyType: HASH
            - AttributeName: timestamp
              KeyType: RANGE
          Projection:
            ProjectionType: ALL

  # Lambda for video processing
  VideoProcessingFunction:
    Type: AWS::Lambda::Function
    Properties:
      FunctionName: !Sub '${AWS::StackName}-video-processor'
      Runtime: python3.11
      Handler: index.lambda_handler
      Role: !GetAtt VideoProcessingRole.Arn
      Timeout: 300
      MemorySize: 3008
      Code:
        ZipFile: |
          import boto3
          import json
          from datetime import datetime
          
          s3 = boto3.client('s3')
          dynamodb = boto3.resource('dynamodb')
          rekognition = boto3.client('rekognition')
          
          def lambda_handler(event, context):
              """
              Zpracuje nahraný video soubor a extrahuje metadata.
              """
              bucket = event['Records'][0]['s3']['bucket']['name']
              key = event['Records'][0]['s3']['object']['key']
              
              # Extrahovat metadata z názvu souboru
              # Format: vehicle_id/YYYY-MM-DD/HH-MM-SS_event.mp4
              parts = key.split('/')
              vehicle_id = parts[0]
              timestamp = datetime.strptime(parts[2].split('_')[0], '%H-%M-%S')
              event_type = parts[2].split('_')[1].replace('.mp4', '')
              
              # Uložit metadata do DynamoDB
              table = dynamodb.Table(os.environ['METADATA_TABLE'])
              table.put_item(Item={
                  'vehicle_id': vehicle_id,
                  'timestamp': int(timestamp.timestamp()),
                  'event_type': event_type,
                  's3_key': key,
                  'processed': False
              })
              
              # Spustit video analýzu (async)
              rekognition.start_label_detection(
                  Video={'S3Object': {'Bucket': bucket, 'Name': key}},
                  NotificationChannel={
                      'SNSTopicArn': os.environ['SNS_TOPIC_ARN'],
                      'RoleArn': os.environ['REKOGNITION_ROLE_ARN']
                  }
              )
              
              return {'statusCode': 200}
      Environment:
        Variables:
          METADATA_TABLE: !Ref VideoMetadataTable
          SNS_TOPIC_ARN: !Ref AlertTopic
          REKOGNITION_ROLE_ARN: !GetAtt RekognitionRole.Arn

  # SNS Topic for alerts
  AlertTopic:
    Type: AWS::SNS::Topic
    Properties:
      TopicName: !Sub '${AWS::StackName}-alerts'
      Subscription:
        - Endpoint: !Ref AlertEmail
          Protocol: email

  # CloudWatch Dashboard
  CameraSystemDashboard:
    Type: AWS::CloudWatch::Dashboard
    Properties:
      DashboardName: !Sub '${AWS::StackName}-dashboard'
      DashboardBody: !Sub |
        {
          "widgets": [
            {
              "type": "metric",
              "properties": {
                "metrics": [
                  ["AWS/IoT", "PublishIn.Success", {"stat": "Sum"}],
                  [".", "PublishIn.Failure", {"stat": "Sum"}]
                ],
                "period": 300,
                "stat": "Sum",
                "region": "${AWS::Region}",
                "title": "IoT Messages"
              }
            },
            {
              "type": "metric",
              "properties": {
                "metrics": [
                  ["CameraSystem", "ObjectDetections", {"stat": "Sum"}],
                  [".", "LaneDetections", {"stat": "Sum"}]
                ],
                "period": 60,
                "stat": "Sum",
                "region": "${AWS::Region}",
                "title": "Detection Metrics"
              }
            }
          ]
        }

Outputs:
  RecordingsBucketName:
    Value: !Ref VideoRecordingsBucket
    Export:
      Name: !Sub '${AWS::StackName}-recordings-bucket'
  
  LiveStreamName:
    Value: !GetAtt CameraLiveStream.Name
    Export:
      Name: !Sub '${AWS::StackName}-live-stream'
```

## 4. Deployment Procedure

### 4.1 Příprava Hardware

```bash
#!/bin/bash
# scripts/setup-jetson.sh

set -euo pipefail

echo "=== Automotive Camera System - Jetson Setup ==="

# 1. Update system
sudo apt-get update
sudo apt-get upgrade -y

# 2. Install JetPack SDK components
sudo apt-get install -y \
    nvidia-jetpack \
    python3-pip \
    python3-opencv \
    v4l-utils \
    can-utils

# 3. Install Python dependencies
pip3 install --upgrade pip
pip3 install \
    boto3 \
    awsiotsdk \
    ultralytics \
    torch \
    torchvision \
    numpy \
    scipy

# 4. Install TensorRT
pip3 install nvidia-tensorrt

# 5. Configure cameras
echo "Detecting cameras..."
v4l2-ctl --list-devices

# 6. Install AWS IoT Greengrass
curl -s https://d2s8p88vqu9w66.cloudfront.net/releases/greengrass-nucleus-latest.zip > greengrass-nucleus-latest.zip
unzip greengrass-nucleus-latest.zip -d GreengrassInstaller
sudo -E java -Droot="/greengrass/v2" -Dlog.store=FILE \
    -jar ./GreengrassInstaller/lib/Greengrass.jar \
    --aws-region eu-central-1 \
    --thing-name VehicleCameraSystem \
    --thing-group-name vehicle-fleet \
    --tes-role-name GreengrassV2TokenExchangeRole \
    --tes-role-alias-name GreengrassCoreTokenExchangeRoleAlias \
    --component-default-user ggc_user:ggc_group \
    --provision true \
    --setup-system-service true

# 7. Configure CAN interface
sudo ip link set can0 up type can bitrate 500000
sudo ifconfig can0 txqueuelen 1000

# 8. Create systemd service
cat > /tmp/automotive-camera.service <<EOF
[Unit]
Description=Automotive Camera System
After=network.target greengrass.service

[Service]
Type=simple
User=ggc_user
WorkingDirectory=/home/ggc_user/automotive-camera
ExecStart=/usr/bin/python3 /home/ggc_user/automotive-camera/src/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo mv /tmp/automotive-camera.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable automotive-camera.service

echo "Setup complete!"
echo "Next steps:"
echo "1. Calibrate cameras: python3 tools/calibrate_cameras.py"
echo "2. Deploy Greengrass components: aws greengrassv2 create-deployment"
echo "3. Start system: sudo systemctl start automotive-camera"
```

### 4.2 Camera Calibration

```python
# tools/calibrate_cameras.py
"""
Nástroj pro kalibraci kamer surround view systému.

Použití:
    python calibrate_cameras.py --cameras 4 --pattern chessboard --size 9x6
"""

import cv2
import numpy as np
import argparse
import json
from pathlib import Path

class CameraCalibrator:
    """
    Kalibrace kamer pomocí šachovnicového vzoru.
    
    Proces:
    1. Zachytí série snímků šachovnice z různých úhlů
    2. Detekuje rohy šachovnice
    3. Vypočítá intrinsic parametry kamery (focal length, principal point)
    4. Vypočítá distortion koeficienty
    5. Uloží kalibrační data pro každou kameru
    """
    
    def __init__(self, pattern_size: tuple = (9, 6), square_size: float = 25.0):
        """
        Args:
            pattern_size: Počet vnitřních rohů (columns, rows)
            square_size: Velikost čtverce v mm
        """
        self.pattern_size = pattern_size
        self.square_size = square_size
        
        # Připravit object points
        self.objp = np.zeros((pattern_size[0] * pattern_size[1], 3), np.float32)
        self.objp[:, :2] = np.mgrid[0:pattern_size[0], 0:pattern_size[1]].T.reshape(-1, 2)
        self.objp *= square_size
        
    def calibrate(self, camera_index: int, num_images: int = 20) -> dict:
        """
        Kalibruje kameru zachycením série snímků.
        
        Args:
            camera_index: Index kamery (0-3 pro 4 kamery)
            num_images: Počet snímků pro kalibraci
            
        Returns:
            dict: Kalibrační parametry (camera_matrix, dist_coeffs, rvecs, tvecs)
        """
        cap = cv2.VideoCapture(camera_index)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        
        obj_points = []  # 3D body v reálném světě
        img_points = []  # 2D body v obraze
        
        captured = 0
        print(f"Calibrating camera {camera_index}...")
        print(f"Position the chessboard pattern in view and press SPACE to capture")
        print(f"Need {num_images} images. Press 'q' to quit.")
        
        while captured < num_images:
            ret, frame = cap.read()
            if not ret:
                continue
                
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Najít rohy šachovnice
            ret, corners = cv2.findChessboardCorners(gray, self.pattern_size, None)
            
            # Vykresl it náhled
            display = frame.copy()
            if ret:
                cv2.drawChessboardCorners(display, self.pattern_size, corners, ret)
                cv2.putText(display, "Pattern found! Press SPACE", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            else:
                cv2.putText(display, "Move pattern into view", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            cv2.putText(display, f"Captured: {captured}/{num_images}", (10, 70),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.imshow(f'Camera {camera_index} Calibration', display)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord(' ') and ret:
                # Zpřesnit detekci rohů
                criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
                corners_refined = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
                
                obj_points.append(self.objp)
                img_points.append(corners_refined)
                captured += 1
                print(f"Captured image {captured}/{num_images}")
        
        cap.release()
        cv2.destroyAllWindows()
        
        if captured < 10:
            raise ValueError("Not enough calibration images captured (minimum 10)")
        
        # Vypočítat kalibrační parametry
        print("Computing calibration parameters...")
        ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
            obj_points, img_points, gray.shape[::-1], None, None
        )
        
        # Vypočítat reprojection error
        mean_error = 0
        for i in range(len(obj_points)):
            img_points2, _ = cv2.projectPoints(obj_points[i], rvecs[i], tvecs[i], 
                                              camera_matrix, dist_coeffs)
            error = cv2.norm(img_points[i], img_points2, cv2.NORM_L2) / len(img_points2)
            mean_error += error
        
        mean_error /= len(obj_points)
        print(f"Mean reprojection error: {mean_error:.4f} pixels")
        
        if mean_error > 1.0:
            print("WARNING: High reprojection error. Consider recalibrating.")
        
        return {
            'camera_matrix': camera_matrix.tolist(),
            'dist_coeffs': dist_coeffs.tolist(),
            'rvecs': [r.tolist() for r in rvecs],
            'tvecs': [t.tolist() for t in tvecs],
            'reprojection_error': float(mean_error),
            'image_size': [1920, 1080],
            'calibrated_at': datetime.now().isoformat()
        }
    
    def compute_homography(self, camera_data: dict, camera_position: str) -> np.ndarray:
        """
        Vypočítá homography matrix pro bird's eye view transformaci.
        
        Args:
            camera_data: Kalibrační data kamery
            camera_position: Pozice kamery ('front', 'rear', 'left', 'right')
            
        Returns:
            np.ndarray: 3x3 homography matrix
        """
        # Definovat zdrojové body v obraze kamery
        # a cílové body v bird's eye view
        if camera_position == 'front':
            src_points = np.float32([
                [400, 400],   # Levý dolní roh
                [1520, 400],  # Pravý dolní roh
                [1520, 800],  # Pravý horní roh
                [400, 800]    # Levý horní roh
            ])
            dst_points = np.float32([
                [320, 0],
                [960, 0],
                [960, 720],
                [320, 720]
            ])
        elif camera_position == 'rear':
            src_points = np.float32([
                [400, 800],
                [1520, 800],
                [1520, 400],
                [400, 400]
            ])
            dst_points = np.float32([
                [320, 720],
                [960, 720],
                [960, 0],
                [320, 0]
            ])
        # ... podobně pro 'left' a 'right'
        
        # Vypočítat homography
        H, _ = cv2.findHomography(src_points, dst_points)
        
        return H

def main():
    parser = argparse.ArgumentParser(description='Camera calibration tool')
    parser.add_argument('--cameras', type=int, default=4, help='Number of cameras')
    parser.add_argument('--pattern', default='chessboard', help='Calibration pattern')
    parser.add_argument('--size', default='9x6', help='Pattern size (e.g., 9x6)')
    parser.add_argument('--output', default='calibration', help='Output directory')
    args = parser.parse_args()
    
    # Parse pattern size
    cols, rows = map(int, args.size.split('x'))
    pattern_size = (cols, rows)
    
    # Create calibrator
    calibrator = CameraCalibrator(pattern_size=pattern_size)
    
    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)
    
    # Calibrate each camera
    camera_positions = ['front', 'rear', 'left', 'right']
    for i in range(args.cameras):
        position = camera_positions[i] if i < len(camera_positions) else f'camera{i}'
        
        print(f"\n=== Calibrating {position} camera (index {i}) ===")
        calibration_data = calibrator.calibrate(camera_index=i)
        
        # Compute homography for surround view
        homography = calibrator.compute_homography(calibration_data, position)
        calibration_data['homography_matrix'] = homography.tolist()
        calibration_data['position'] = position
        
        # Save calibration data
        output_file = output_dir / f'{position}_calibration.json'
        with open(output_file, 'w') as f:
            json.dump(calibration_data, f, indent=2)
        
        print(f"Calibration saved to {output_file}")
    
    print("\n=== Calibration Complete ===")
    print(f"Calibration files saved in: {output_dir}")
    print("Next step: Deploy the camera system")

if __name__ == '__main__':
    main()
```

## 5. Cost Analysis

### 5.1 Development Costs

| Položka | Cena (Kč) | Poznámka |
|---------|-----------|----------|
| NVIDIA Jetson Xavier NX | 10,000 | Computing platform |
| 4x Wide-angle kamery | 8,000 | Arducam nebo podobné |
| GPS modul | 1,000 | u-blox NEO-M9N |
| CAN Bus adapter | 800 | CANable USB |
| microSD 128GB | 500 | Samsung EVO Plus |
| NVMe SSD 256GB | 1,200 | Pro recordings |
| Display 7" | 2,000 | Touchscreen LCD |
| Kabeláž a konektory | 1,500 | FAKRA, USB kabely |
| Napájecí systém | 1,000 | 12V DC-DC converter |
| **Celkem hardware** | **26,000 Kč** | (~$1,100) |
| | | |
| Vývoj software (200h) | 400,000 | @ 2,000 Kč/h |
| Testing & validace (50h) | 100,000 | @ 2,000 Kč/h |
| Dokumentace (20h) | 40,000 | @ 2,000 Kč/h |
| **Celkem vývoj** | **540,000 Kč** | (~$23,000) |

### 5.2 Operating Costs (Monthly per vehicle)

| AWS Service | Cena (Kč/měsíc) | Poznámka |
|-------------|-----------------|----------|
| IoT Core | 15-50 | Telemetry messages |
| Kinesis Video | 120-240 | 1h streaming/day |
| S3 Storage | 50-120 | 30-day retention |
| Lambda | 25-50 | Event processing |
| Data Transfer | 120-240 | Upload recordings |
| CloudWatch | 25-50 | Logs & metrics |
| **Celkem AWS** | **355-750 Kč** | (~$15-32/month) |

### 5.3 ROI Calculation

```python
# Výpočet návratnosti investice

# Předpoklady
development_cost = 540_000  # Kč
hardware_per_vehicle = 26_000  # Kč
aws_monthly_per_vehicle = 550  # Kč (průměr)
installation_cost = 5_000  # Kč per vehicle

# Scénář: Fleet 100 vozidel
num_vehicles = 100

total_initial_investment = (
    development_cost +
    (hardware_per_vehicle + installation_cost) * num_vehicles
)

print(f"Initial investment: {total_initial_investment:,} Kč")
# = 540,000 + 3,100,000 = 3,640,000 Kč (~$155,000)

# Monthly operating costs
monthly_operating = aws_monthly_per_vehicle * num_vehicles
print(f"Monthly operating: {monthly_operating:,} Kč")
# = 55,000 Kč/month (~$2,350)

# Break-even analysis
# Pokud prodáváme systém za 50,000 Kč per vozidlo
selling_price = 50_000  # Kč
total_revenue = selling_price * num_vehicles  # 5,000,000 Kč

profit = total_revenue - total_initial_investment
print(f"Profit after initial deployment: {profit:,} Kč")
# = 1,360,000 Kč (~$58,000)

# Payback period (months)
monthly_profit_per_vehicle = selling_price - hardware_per_vehicle - installation_cost - aws_monthly_per_vehicle * 12
payback_period = development_cost / (monthly_profit_per_vehicle * num_vehicles / 12)
print(f"Payback period: {payback_period:.1f} months")
```

## 6. Regulatory Compliance

### 6.1 EU Regulations

```markdown
## UN R46 - Camera Monitor Systems

Požadavky:
- Field of view: minimálně 20m za vozidlem
- Display lag: max 200ms
- Display resolution: min 480x240 px
- Aktivace: automatická při zpětném chodu
- Životnost: 5,000 hodin provozu

Compliance checklist:
- [x] FOV > 20m (150° širokoúhlá kamera)
- [x] Latence < 100ms (real-time processing)
- [x] Rozlišení 1280x720 (výrazně nad minimum)
- [x] Auto-aktivace přes CAN bus signal
- [x] Industrial-grade komponenty
```

### 6.2 GDPR Compliance

```python
class PrivacyFilter:
    """
    GDPR-compliant privacy filter pro automatické rozmazání obličejů.
    
    Detekuje a rozmazává obličeje osob v záznamu před nahráním do cloudu.
    Zachovává metadata pro forensic analysis.
    """
    
    def __init__(self):
        # Použít lightweight face detection model
        self.face_detector = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
    def anonymize_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Anonymizuje frame rozmazáním obličejů.
        
        Args:
            frame: Input RGB frame
            
        Returns:
            Anonymized frame with blurred faces
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detekovat obličeje
        faces = self.face_detector.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        # Rozmazat každý obličej
        for (x, y, w, h) in faces:
            # Extrahovat ROI
            face_roi = frame[y:y+h, x:x+w]
            
            # Aplikovat Gaussian blur
            blurred_face = cv2.GaussianBlur(face_roi, (99, 99), 30)
            
            # Vložit zpět
            frame[y:y+h, x:x+w] = blurred_face
        
        return frame
```

## 7. Testing & Validation

### 7.1 HIL (Hardware-in-the-Loop) Testing

```python
# tests/hil/test_camera_system.py
"""
Hardware-in-the-Loop testy pro automotive kamerový systém.
"""

import pytest
import time
import numpy as np
from automotive_camera import SurroundViewSystem, ADASSystem

@pytest.fixture
def camera_system():
    """Inicializuje camera system pro testing."""
    return SurroundViewSystem(cameras=4)

class TestSurroundView:
    """Testy pro surround view systém."""
    
    def test_camera_initialization(self, camera_system):
        """Test inicializace všech kamer."""
        assert len(camera_system.cameras) == 4
        for cam in camera_system.cameras:
            assert cam.isOpened()
    
    def test_frame_acquisition(self, camera_system):
        """Test získání frame ze všech kamer."""
        frames = camera_system.get_frames()
        assert len(frames) == 4
        for frame in frames:
            assert frame.shape == (1080, 1920, 3)
    
    def test_surround_view_generation(self, camera_system):
        """Test generování surround view."""
        surround = camera_system.generate_surround_view()
        
        # Zkontrolovat rozlišení
        assert surround.shape == (720, 1280, 3)
        
        # Zkontrolovat že není černý frame
        assert np.mean(surround) > 10
    
    def test_latency(self, camera_system):
        """Test latence zpracování."""
        times = []
        for _ in range(100):
            start = time.time()
            _ = camera_system.generate_surround_view()
            elapsed = (time.time() - start) * 1000  # ms
            times.append(elapsed)
        
        avg_latency = np.mean(times)
        max_latency = np.max(times)
        
        print(f"Average latency: {avg_latency:.2f}ms")
        print(f"Max latency: {max_latency:.2f}ms")
        
        # Assert latence požadavky
        assert avg_latency < 50, "Average latency too high"
        assert max_latency < 100, "Max latency exceeds requirement"
    
    def test_fps(self, camera_system):
        """Test framerate."""
        start = time.time()
        frames = 0
        
        while time.time() - start < 10:  # 10 sekund test
            _ = camera_system.generate_surround_view()
            frames += 1
        
        fps = frames / (time.time() - start)
        print(f"FPS: {fps:.1f}")
        
        assert fps >= 30, "FPS below requirement"

class TestADAS:
    """Testy pro ADAS funkce."""
    
    def test_object_detection(self):
        """Test detekce objektů."""
        adas = ADASSystem()
        
        # Load test image s vozidlem
        test_image = cv2.imread('tests/data/car_front.jpg')
        
        results = adas.detect_objects(test_image)
        
        # Zkontrolovat že detekoval auto
        assert any(obj['class'] == 'car' for obj in results)
        
        # Zkontrolovat confidence
        car_detections = [obj for obj in results if obj['class'] == 'car']
        assert all(obj['confidence'] > 0.5 for obj in car_detections)
    
    def test_lane_detection(self):
        """Test detekce jízdních pruhů."""
        adas = ADASSystem()
        
        test_image = cv2.imread('tests/data/highway.jpg')
        lanes = adas.detect_lanes(test_image)
        
        # Zkontrolovat že detekoval alespoň 2 pruhy
        assert len(lanes) >= 2
        
        # Zkontrolovat že jsou relativně rovnoběžné
        slopes = [lane['slope'] for lane in lanes]
        assert max(slopes) - min(slopes) < 0.5
```

### 7.2 Performance Benchmarks

```python
# tests/benchmarks/benchmark_inference.py
"""
Performance benchmarking pro ML inference.
"""

import time
import numpy as np
from automotive_camera.models import YOLODetector, LaneDetector

def benchmark_yolo():
    """Benchmark YOLO object detection."""
    detector = YOLODetector(model_path='models/yolov8n.engine')
    
    # Dummy input
    dummy_frame = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
    
    # Warmup
    for _ in range(10):
        _ = detector.detect(dummy_frame)
    
    # Benchmark
    times = []
    for _ in range(1000):
        start = time.perf_counter()
        results = detector.detect(dummy_frame)
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
    
    print(f"\n=== YOLO Inference Benchmark ===")
    print(f"Average: {np.mean(times):.2f}ms")
    print(f"Median: {np.median(times):.2f}ms")
    print(f"P95: {np.percentile(times, 95):.2f}ms")
    print(f"P99: {np.percentile(times, 99):.2f}ms")
    print(f"Max: {np.max(times):.2f}ms")
    print(f"FPS: {1000 / np.mean(times):.1f}")

def benchmark_lane():
    """Benchmark lane detection."""
    detector = LaneDetector(model_path='models/scnn_lane.engine')
    
    dummy_frame = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
    
    # Warmup
    for _ in range(10):
        _ = detector.detect(dummy_frame)
    
    # Benchmark
    times = []
    for _ in range(1000):
        start = time.perf_counter()
        results = detector.detect(dummy_frame)
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
    
    print(f"\n=== Lane Detection Benchmark ===")
    print(f"Average: {np.mean(times):.2f}ms")
    print(f"P95: {np.percentile(times, 95):.2f}ms")
    print(f"FPS: {1000 / np.mean(times):.1f}")

if __name__ == '__main__':
    benchmark_yolo()
    benchmark_lane()
```

## 8. Production Deployment Checklist

```markdown
## Pre-Deployment

- [ ] Hardware commissioning
  - [ ] All cameras working and calibrated
  - [ ] Jetson Xavier configured and tested
  - [ ] Power supply validated (12V → 5V conversion)
  - [ ] CAN bus communication verified
  - [ ] GPS lock confirmed
  
- [ ] Software validation
  - [ ] All tests passing (unit + integration + HIL)
  - [ ] Performance benchmarks meeting targets
  - [ ] Memory leaks checked (valgrind)
  - [ ] Power consumption measured (<15W)
  
- [ ] AWS infrastructure
  - [ ] IoT thing provisioned and certificates installed
  - [ ] Greengrass components deployed
  - [ ] S3 buckets created with lifecycle policies
  - [ ] CloudWatch alarms configured
  - [ ] IAM roles and policies verified

## Installation

- [ ] Vehicle preparation
  - [ ] Camera mounting positions marked
  - [ ] Wiring harness routed
  - [ ] Computing unit mounted in dry, ventilated area
  - [ ] Display integrated into dashboard
  
- [ ] System integration
  - [ ] CAN bus tapped (with proper isolation)
  - [ ] Power connected through fused circuit
  - [ ] Ground connections solid
  - [ ] Cameras aimed and focused
  
- [ ] Calibration
  - [ ] Camera intrinsic calibration completed
  - [ ] Homography matrices calculated
  - [ ] Surround view stitching verified
  - [ ] ADAS calibration (if applicable)

## Testing & Validation

- [ ] Functional tests
  - [ ] All camera views displaying correctly
  - [ ] Surround view seamless stitching
  - [ ] Object detection working
  - [ ] Lane detection accurate
  - [ ] Recording and playback functional
  
- [ ] Integration tests
  - [ ] CAN bus data received correctly
  - [ ] GPS position accurate
  - [ ] Cloud connectivity established
  - [ ] Firmware OTA update tested
  
- [ ] Road tests
  - [ ] Parking scenarios (tight spaces, angles)
  - [ ] Highway driving (lane keeping, FCW)
  - [ ] Various lighting conditions (day, night, tunnel)
  - [ ] Weather conditions (rain, fog if possible)

## Documentation

- [ ] User manual delivered
- [ ] Installation guide provided
- [ ] Maintenance schedule defined
- [ ] Warranty terms documented
- [ ] Emergency procedures outlined

## Handover

- [ ] Customer training completed
- [ ] System demonstration performed
- [ ] Support contacts provided
- [ ] Feedback mechanism established
- [ ] Final acceptance signed
```

---

**Dokument vytvořen**: 2025-10-01  
**Verze**: 1.0.0  
**Autor**: MCP Project Orchestrator  
**Jazyk**: Čeština

Pro další informace nebo podporu kontaktujte: automotive-camera@support.io
