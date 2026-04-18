import cv2
import json
import mediapipe as mp
from sqlalchemy.orm import Session
import models

mp_pose = mp.solutions.pose

def process_video(db: Session, swing_id: int, video_path: str):
    """
    영상 파일에서 관절 점(Keypoints)을 추출하여 DB에 저장합니다.
    실제 VideoPose3D(2D->3D) 모델 환경 세팅은 복잡하고 무거우므로, 
    여기서는 MediaPipe Pose의 z 좌표(내장 3D 추정기능)를 활용하여 3D 관절 모델을 대체 구현합니다.
    """
    cap = cv2.VideoCapture(video_path)
    
    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5, model_complexity=1) as pose:
        frame_idx = 0
        while cap.isOpened():
            success, image = cap.read()
            if not success:
                break
                
            # 성능 향상을 위해 이미지 쓰기 불가 설정
            image.flags.writeable = False
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = pose.process(image_rgb)
            
            if results.pose_landmarks:
                # 33개의 각 관절(Landmark) 데이터를 x, y, z 리스트 딕셔너리로 추출
                # Three.js 등에서 활용하기 쉬운 형태로 변환
                keypoints = []
                for lm in results.pose_landmarks.landmark:
                    # x, y 보정 (카메라 픽셀이나 뷰포트에 맞출 수 있게 Normalize된 값을 저장)
                    # Three.js 축에 맞게 Y를 반전시키거나 Z의 깊이를 조정하여 사용합니다.
                    # MediaPipe의 Z는 골반 중심 기준 상대적인 깊이입니다.
                    keypoints.append({
                        "x": lm.x,
                        "y": -lm.y, # Three.js 공간은 Y가 위쪽
                        "z": lm.z,
                        "visibility": lm.visibility
                    })
                
                # DB 저장
                new_pose = models.Pose(
                    swing_id=swing_id,
                    frame_index=frame_idx,
                    keypoints_json=json.dumps(keypoints)
                )
                db.add(new_pose)
            
            frame_idx += 1
            
        db.commit()
    cap.release()
