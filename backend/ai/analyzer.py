import json
import math
import numpy as np
from sqlalchemy.orm import Session
from .. import models

# ==========================================
# 0. MediaPipe 주요 관절 인덱스 및 V2 전처리 로직 일부
# ==========================================
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12
LEFT_HIP = 23
RIGHT_HIP = 24
LEFT_WRIST = 15
RIGHT_WRIST = 16

def ema_smoothing(frames, alpha=0.3):
    if not frames: return frames
    smoothed = json.loads(json.dumps([frames[0]]))
    for i in range(1, len(frames)):
        current_frame = frames[i]
        prev_smoothed = smoothed[i - 1]
        new_smoothed_frame = []
        for j in range(len(current_frame)):
            kp_curr = current_frame[j]
            kp_prev = prev_smoothed[j]
            new_kp = {
                "x": alpha * kp_curr["x"] + (1 - alpha) * kp_prev["x"],
                "y": alpha * kp_curr["y"] + (1 - alpha) * kp_prev["y"],
                "z": alpha * kp_curr["z"] + (1 - alpha) * kp_prev["z"],
                "visibility": kp_curr["visibility"]
            }
            new_smoothed_frame.append(new_kp)
        smoothed.append(new_smoothed_frame)
    return smoothed

def remove_outliers(frames, threshold_std=2.0):
    num_frames, num_keypoints = len(frames), len(frames[0])
    for j in range(num_keypoints):
        x_vals = [frames[i][j]['x'] for i in range(num_frames)]
        y_vals = [frames[i][j]['y'] for i in range(num_frames)]
        z_vals = [frames[i][j]['z'] for i in range(num_frames)]
        mean_x, std_x = np.mean(x_vals), np.std(x_vals)
        mean_y, std_y = np.mean(y_vals), np.std(y_vals)
        mean_z, std_z = np.mean(z_vals), np.std(z_vals)
        for i in range(num_frames):
            if abs(frames[i][j]['x'] - mean_x) > threshold_std * std_x: frames[i][j]['x'] = mean_x
            if abs(frames[i][j]['y'] - mean_y) > threshold_std * std_y: frames[i][j]['y'] = mean_y
            if abs(frames[i][j]['z'] - mean_z) > threshold_std * std_z: frames[i][j]['z'] = mean_z
    return frames

def normalize_pose(frames):
    normalized_frames = []
    for frame in frames:
        hip_center_x = (frame[LEFT_HIP]['x'] + frame[RIGHT_HIP]['x']) / 2.0
        hip_center_y = (frame[LEFT_HIP]['y'] + frame[RIGHT_HIP]['y']) / 2.0
        hip_center_z = (frame[LEFT_HIP]['z'] + frame[RIGHT_HIP]['z']) / 2.0
        shoulder_dist = math.sqrt(
            (frame[LEFT_SHOULDER]['x'] - frame[RIGHT_SHOULDER]['x'])**2 +
            (frame[LEFT_SHOULDER]['y'] - frame[RIGHT_SHOULDER]['y'])**2 +
            (frame[LEFT_SHOULDER]['z'] - frame[RIGHT_SHOULDER]['z'])**2
        )
        scale_factor = shoulder_dist if shoulder_dist > 0 else 1.0
        norm_frame = []
        for kp in frame:
            norm_frame.append({
                "x": (kp['x'] - hip_center_x) / scale_factor,
                "y": (kp['y'] - hip_center_y) / scale_factor,
                "z": (kp['z'] - hip_center_z) / scale_factor,
                "visibility": kp['visibility']
            })
        normalized_frames.append(norm_frame)
    return normalized_frames

def get_rotation(pose, left_idx, right_idx):
    dx = pose[right_idx]['x'] - pose[left_idx]['x']
    dz = pose[right_idx]['z'] - pose[left_idx]['z']
    return abs(math.degrees(math.atan2(dz, dx)))

def detect_swing_phases(frames):
    wrist_y_coords, wrist_velocities = [], []
    for i in range(len(frames)):
        avg_wrist_y = (frames[i][LEFT_WRIST]['y'] + frames[i][RIGHT_WRIST]['y']) / 2.0
        wrist_y_coords.append(avg_wrist_y)
    
    top_index = int(np.argmax(wrist_y_coords))
    impact_index = top_index
    if top_index < len(frames) - 1:
        impact_index = top_index + int(np.argmin(wrist_y_coords[top_index:]))
        
    return {"start": 0, "top": top_index, "impact": impact_index}

# ==========================================
# [V4 1] 피처 추출 (Data Extraction)
# ==========================================
def extract_swing_features(frames, phases):
    top_idx = phases["top"]
    impact_idx = phases["impact"]
    
    # 1. 어깨/골반 회전 (Top 기준)
    top_frame = frames[top_idx]
    shoulder_rot = get_rotation(top_frame, LEFT_SHOULDER, RIGHT_SHOULDER)
    hip_rot = get_rotation(top_frame, LEFT_HIP, RIGHT_HIP)
    x_factor = abs(shoulder_rot - hip_rot)
    
    # 2. 체중 이동 (어드레스 -> 탑 -> 임팩트 간 골반 이동거리)
    address_hip_x = (frames[0][LEFT_HIP]['x'] + frames[0][RIGHT_HIP]['x']) / 2.0
    impact_hip_x = (frames[impact_idx][LEFT_HIP]['x'] + frames[impact_idx][RIGHT_HIP]['x']) / 2.0
    # 정규화된 값(어깨넓이 1 단위 대비 이동) - 보통 골프에서 백스윙시 우측(X증가, 또는 상황에 따라)이동 후 좌측 이동
    weight_shift = abs(impact_hip_x - address_hip_x) * 100 # 임의의 스케일업
    
    # 3. 템포 (백스윙 소요 프레임 / 다운스윙 소요 프레임)
    # 실제로는 초당 프레임(FPS) 처리가 들어가야하나 단위가 소거되므로 프레임 비율 연산 사용
    backswing_time = float(top_idx) 
    downswing_time = float(impact_idx - top_idx)
    tempo = backswing_time / downswing_time if downswing_time > 0 else 0
    
    # 4. 손 속도 (Top -> Impact 손의 평균 변위)
    hand_dist = math.sqrt(
        (frames[impact_idx][RIGHT_WRIST]['x'] - top_frame[RIGHT_WRIST]['x'])**2 +
        (frames[impact_idx][RIGHT_WRIST]['y'] - top_frame[RIGHT_WRIST]['y'])**2
    )
    hand_speed = (hand_dist / downswing_time) * 100 if downswing_time > 0 else 0

    return {
        "shoulder_rotation_max": round(shoulder_rot, 1),
        "hip_rotation_max": round(hip_rot, 1),
        "x_factor": round(x_factor, 1),
        "weight_shift": round(weight_shift, 1),
        "swing_tempo": round(tempo, 2),
        "hand_speed": round(hand_speed, 1)
    }

# ==========================================
# [V4 2 & 3] 기준값 정의 및 점수화 알고리즘
# ==========================================
PRO_REFERENCE = {
    "shoulder_rotation_max": {"min": 85, "max": 110, "weight": 0.20},
    "hip_rotation_max": {"min": 40, "max": 60, "weight": 0.15},
    "x_factor": {"min": 35, "max": 55, "weight": 0.30},
    "weight_shift": {"min": 5, "max": 20, "weight": 0.15},
    "swing_tempo": {"min": 2.5, "max": 3.5, "weight": 0.10},
    "hand_speed": {"min": 15, "max": 40, "weight": 0.10}  # 임의 스케일 추정치 적용
}

def score_metric(value, min_val, max_val):
    """
    해당 값이 권장구간 안에 있으면 100점. 벗어나면 차이나는 비율만큼 점수를 깎습니다.
    """
    if value < min_val:
        error = (min_val - value) / min_val
    elif value > max_val:
        error = (value - max_val) / max_val
    else:
        return 100
    
    # 페널티 강도(100을 곱함) 이후 최저를 0으로.
    return max(0, 100 - (error * 100))

def calculate_total_score(metrics):
    total_score = 0
    scores = {}
    for key, spec in PRO_REFERENCE.items():
        val = metrics.get(key, 0)
        s = score_metric(val, spec["min"], spec["max"])
        scores[key] = round(s, 1)
        total_score += (s * spec["weight"])
    return round(total_score, 1), scores

# ==========================================
# [V4 4] 자동 문제 진단
# ==========================================
def detect_issues(scores, metrics):
    issues = []
    # 80점 이하 항목을 심각한 결함으로 판단
    if scores.get("x_factor", 100) < 80:
        issues.append(f"X-Factor 부족 ({metrics['x_factor']}°): 꼬루 부족으로 비거리가 손실되고 있습니다.")
    
    if scores.get("weight_shift", 100) < 80:
        issues.append(f"체중 이동 불안정 (변위: {metrics['weight_shift']}): 올바른 궤도를 탈 수 없습니다.")
        
    if scores.get("swing_tempo", 100) < 80:
        if metrics.get("swing_tempo", 0) < 2.5:
            issues.append(f"템포 너무 빠름 (비율 {metrics['swing_tempo']}): 백스윙 타이밍이 충분하지 않습니다.")
        else:
            issues.append(f"템포 느림 (비율 {metrics['swing_tempo']}): 다운스윙의 타격 속도 비율이 저하되었습니다.")
            
    if not issues:
        issues.append("전반적인 수치가 양호합니다. 미세 교정에 집중하세요.")
        
    return issues


# ==========================================
# 통합 및 API 반환
# ==========================================
def analyze_swing(db: Session, swing_id: int):
    # 1. 포즈 로드 및 전처리
    poses = db.query(models.Pose).filter(models.Pose.swing_id == swing_id).order_by(models.Pose.frame_index).all()
    if not poses: return None
    
    raw_frames = [json.loads(p.keypoints_json) for p in poses]
    norm_frames = normalize_pose(remove_outliers(ema_smoothing(raw_frames)))
    
    # 데이터 강제 업데이트 (프론트 뷰어를 위해)
    for i, p in enumerate(poses):
        p.keypoints_json = json.dumps(norm_frames[i])
    db.commit()

    # 2. 분석 시작
    phases = detect_swing_phases(norm_frames)
    metrics = extract_swing_features(norm_frames, phases)
    total_score, individual_scores = calculate_total_score(metrics)
    issues = detect_issues(individual_scores, metrics)
    
    # 3. 데이터 기록 비교 (Personalization)
    swing = db.query(models.Swing).filter(models.Swing.id == swing_id).first()
    # 유저의 예전 스윙들 가져오기
    prev_swing = db.query(models.Swing).join(models.Analysis).filter(
        models.Swing.user_id == swing.user_id, models.Swing.id < swing_id
    ).order_by(models.Swing.id.desc()).first()
    
    improvement = 0
    if prev_swing and prev_swing.analysis:
        try:
            prev_data = json.loads(prev_swing.analysis[0].result_json)
            improvement = round(total_score - prev_data["total_score"], 1)
        except Exception:
            pass

    # 4. Result 저장 및 반환
    result_dict = {
        "total_score": total_score,
        "improvement": improvement,
        "metrics": metrics,
        "scores": individual_scores,
        "issues": issues,
        "summary": f"완벽도 Score {total_score}점 (이전 대비 체득: {improvement}점 상승/하락)"
    }
    
    analysis_obj = models.Analysis(swing_id=swing_id, result_json=json.dumps(result_dict, ensure_ascii=False))
    db.add(analysis_obj)
    db.commit()
    db.refresh(analysis_obj)
    
    return analysis_obj
