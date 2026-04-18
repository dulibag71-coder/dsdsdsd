import React, { useState, useEffect } from 'react';
import { StyleSheet, Text, View, TouchableOpacity, ActivityIndicator, Dimensions } from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { BlurView } from 'expo-blur';
import { useFonts, Inter_400Regular, Inter_500Medium } from '@expo-google-fonts/inter';
import { SpaceGrotesk_700Bold, SpaceGrotesk_500Medium } from '@expo-google-fonts/space-grotesk';

import { getOrCreateUser, uploadVideo, getPose, analyzeSwing, getLesson } from './src/api';
import ThreeViewer from './src/components/ThreeViewer';

const { width, height } = Dimensions.get('window');

// Kinetic Grid Colors
const SURFACE = '#0b1326';
const SURFACE_LOW = 'rgba(30, 38, 56, 0.7)'; // fallback for non-blur
const PRIMARY_FIXED = '#9ffb06';
const ON_PRIMARY_FIXED = '#102000';
const ON_SURFACE = '#ffffff';
const ON_SURFACE_VARIANT = '#8a95a5';
const ERROR = '#ffb4ab';

export default function App() {
  const [fontsLoaded] = useFonts({
    Inter_400Regular,
    Inter_500Medium,
    SpaceGrotesk_700Bold,
    SpaceGrotesk_500Medium,
  });

  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);
  const [statusText, setStatusText] = useState('시스템 대기 중');

  const [swingId, setSwingId] = useState(null);
  const [poses, setPoses] = useState([]);
  const [comparisonPoses, setComparisonPoses] = useState(null); 
  const [showComparison, setShowComparison] = useState(false);
  
  const [analysisData, setAnalysisData] = useState(null);
  const [lessonObject, setLessonObject] = useState(null);

  useEffect(() => {
    async function initUser() {
      try {
        const u = await getOrCreateUser("elite_golfer@kinetic.io");
        setUser(u);
        setStatusText('서버 접속 완료');
      } catch (e) {
        setStatusText('서버 연결 실패');
      }
    }
    initUser();
  }, []);

  const selectAndUploadVideo = async () => {
    if (!user) return;
    try {
      let result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Videos,
        allowsEditing: true,
        quality: 1,
      });

      if (!result.canceled && result.assets.length > 0) {
        setLoading(true);
        setStatusText('영상 최적화 및 업로드 중...');
        const asset = result.assets[0];
        const filename = asset.uri.split('/').pop();
        
        const swingResult = await uploadVideo(user.id, asset.uri, filename, "video/mp4");
        setSwingId(swingResult.id);
        setStatusText('자세 추출 및 AI 모델링 중...');
        
        try {
          const poseData = await getPose(swingResult.id);
          setPoses(poseData);
          setStatusText('3D 관절 매핑 완료');
          setLoading(false);
        } catch (err) {
          setStatusText('서버 데이터 수신 오류');
          setLoading(false);
        }
      }
    } catch (error) {
      setStatusText('사용자 취소됨');
      setLoading(false);
    }
  };

  const getAnalysisAndLesson = async () => {
    if (!swingId) return;
    setLoading(true);
    setStatusText('물리 엔진 점수화 진행 중...');
    try {
      const anl = await analyzeSwing(swingId);
      setAnalysisData(JSON.parse(anl.result_json));
      
      setStatusText('데이터 기반 AI 레슨 생성 중...');
      const lsn = await getLesson(swingId);
      
      try {
        const parsedLesson = JSON.parse(lsn.lesson_text);
        setLessonObject(parsedLesson);
      } catch {
        setLessonObject(null);
      }
      
      setStatusText('AI 코칭 완료');
    } catch (e) {
      setStatusText('서버 분석 실패 (타임아웃)');
    } finally {
      setLoading(false);
    }
  };

  if (!fontsLoaded) {
    return <View style={{ flex: 1, backgroundColor: SURFACE, justifyContent: 'center' }}><ActivityIndicator color={PRIMARY_FIXED}/></View>;
  }

  // 엣지 케이스 처리 로직
  const xFactor = analysisData?.metrics?.top_x_factor_deg || "N/A";
  const shoulderRot = analysisData?.metrics?.top_shoulder_rotation_deg || "N/A";

  return (
    <View style={styles.container}>
      {/* 3D Viewer acts as the background well, breaking the fourth wall */}
      <View style={styles.threeCanvasWell}>
        <ThreeViewer poses={poses} comparisonPoses={showComparison ? comparisonPoses : null} />
      </View>

      {/* Floating HUD Modules - Asymmetric Layout */}
      
      {/* Top Left Header */}
      <View style={styles.headerStack}>
        <Text style={styles.title}>KINETIC<Text style={{color: PRIMARY_FIXED}}>GRID</Text></Text>
        <Text style={styles.statusLabel}>{statusText}</Text>
      </View>

      {/* Action Sidebar - Right aligned, tight */}
      <View style={styles.actionSidebar}>
        <TouchableOpacity style={styles.primaryButton} onPress={selectAndUploadVideo} disabled={loading}>
          <Text style={styles.primaryButtonText}>업로드</Text>
          <Text style={styles.primaryButtonSub}>내 스윙 분석하기</Text>
        </TouchableOpacity>

        <BlurView intensity={20} style={[styles.secondaryButtonBox, (!swingId || poses.length === 0) && {opacity: 0.5}]} tint="dark">
            <TouchableOpacity onPress={getAnalysisAndLesson} disabled={loading || !swingId || poses.length === 0}>
                <Text style={styles.secondaryButtonText}>AI 정밀 분석 실행</Text>
            </TouchableOpacity>
        </BlurView>
      </View>

      {/* Extreme Scale Data Display - Bottom Left */}
      {analysisData && (
        <BlurView intensity={60} tint="dark" style={styles.dataDisplayWell}>
            <View style={styles.chip}>
                <Text style={styles.chipText}>현재 스코어 ({analysisData.improvement >= 0 ? '+' : ''}{analysisData.improvement}점)</Text>
            </View>
            <Text style={styles.displayLg}>{analysisData.total_score}</Text>
            <Text style={styles.labelMd}>종합 숙련도 분석</Text>
            
            <View style={{ height: 16 }} />
            <Text style={styles.displayMd}>{analysisData.metrics?.x_factor || 0}°</Text>
            <Text style={styles.labelMd}>X-Factor 코일링 (점수: {analysisData.scores?.x_factor || 0})</Text>
        </BlurView>
      )}

      {/* Narrative Voice Lesson Deck - Bottom Right overlapping */}
      {lessonObject ? (
        <BlurView intensity={80} tint="dark" style={styles.narrativeDeck}>
            <Text style={styles.narrativeTitle}>AI 코치 리포트</Text>
            <Text style={styles.narrativeHighlight}>{lessonObject.summary}</Text>
            <Text style={styles.narrativeBody}><Text style={{color:PRIMARY_FIXED}}>진단:</Text> {lessonObject.details}</Text>
            <Text style={styles.narrativeBody}><Text style={{color:'#03A9F4'}}>교정:</Text> {lessonObject.fix}</Text>
            <Text style={styles.narrativeBody}><Text style={{color:'#E91E63'}}>연습:</Text> {lessonObject.drill}</Text>
        </BlurView>
      ) : null}

      {/* Loading Overlay */}
      {loading && (
        <View style={styles.loadingOverlay}>
            <ActivityIndicator size="large" color={PRIMARY_FIXED} />
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: SURFACE,
  },
  threeCanvasWell: {
    ...StyleSheet.absoluteFillObject, // Fills entire background allowing overlap
    zIndex: 0,
  },
  headerStack: {
    position: 'absolute',
    top: 60,
    left: 24,
    zIndex: 10,
  },
  title: {
    fontFamily: 'SpaceGrotesk_700Bold',
    fontSize: 28,
    color: ON_SURFACE,
    letterSpacing: 2,
  },
  statusLabel: {
    fontFamily: 'SpaceGrotesk_500Medium',
    fontSize: 12,
    color: ON_SURFACE_VARIANT,
    letterSpacing: 1,
    marginTop: 4,
  },
  actionSidebar: {
    position: 'absolute',
    top: 60,
    right: 24,
    width: 140,
    zIndex: 10,
  },
  primaryButton: {
    backgroundColor: PRIMARY_FIXED,
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderRadius: 12, // xl
    marginBottom: 16,
    alignItems: 'flex-end',
    borderWidth: 0,
    // High-gloss glow via shadow
    shadowColor: PRIMARY_FIXED,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.4,
    shadowRadius: 12,
    elevation: 8,
  },
  primaryButtonText: {
    fontFamily: 'SpaceGrotesk_700Bold',
    fontSize: 18,
    color: ON_PRIMARY_FIXED,
  },
  primaryButtonSub: {
    fontFamily: 'Inter_500Medium',
    fontSize: 9,
    color: ON_PRIMARY_FIXED,
    opacity: 0.7,
  },
  secondaryButtonBox: {
    borderRadius: 12,
    overflow: 'hidden',
    padding: 14,
    marginBottom: 12,
    backgroundColor: 'rgba(255,255,255,0.05)', // Fallback for glass
    // Ghost Border
    borderWidth: 1,
    borderColor: 'rgba(65, 74, 52, 0.15)',
  },
  secondaryButtonText: {
    fontFamily: 'SpaceGrotesk_700Bold',
    fontSize: 12,
    color: ON_SURFACE,
    textAlign: 'right',
  },
  dataDisplayWell: {
    position: 'absolute',
    bottom: 40,
    left: 24,
    width: 180,
    padding: 24,
    borderRadius: 16,
    overflow: 'hidden',
    backgroundColor: 'rgba(11, 19, 38, 0.4)',
    borderWidth: 1,
    borderColor: 'rgba(65, 74, 52, 0.15)',
    zIndex: 10,
  },
  displayLg: {
    fontFamily: 'SpaceGrotesk_700Bold',
    fontSize: 56,
    color: ON_SURFACE,
    lineHeight: 60,
  },
  displayMd: {
    fontFamily: 'SpaceGrotesk_700Bold',
    fontSize: 32,
    color: ON_SURFACE,
    lineHeight: 36,
  },
  labelMd: {
    fontFamily: 'Inter_500Medium',
    fontSize: 10,
    color: ON_SURFACE_VARIANT,
    letterSpacing: 2,
    marginTop: 2,
  },
  chip: {
    backgroundColor: 'rgba(159, 251, 6, 0.15)',
    paddingVertical: 4,
    paddingHorizontal: 8,
    borderRadius: 20,
    alignSelf: 'flex-start',
    marginBottom: 12,
    borderWidth: 1,
    borderColor: 'rgba(159, 251, 6, 0.3)',
  },
  chipText: {
    fontFamily: 'Inter_500Medium',
    fontSize: 9,
    color: PRIMARY_FIXED,
  },
  narrativeDeck: {
    position: 'absolute',
    bottom: 40,
    right: 24,
    width: width - 240, // Asymmetric overlapping
    padding: 24,
    borderRadius: 16,
    overflow: 'hidden',
    backgroundColor: 'rgba(30, 38, 56, 0.8)',
    borderWidth: 1,
    borderColor: 'rgba(65, 74, 52, 0.15)',
    zIndex: 10,
  },
  narrativeTitle: {
    fontFamily: 'SpaceGrotesk_700Bold',
    fontSize: 14,
    color: ON_SURFACE,
    letterSpacing: 1,
    marginBottom: 8,
  },
  narrativeHighlight: {
    fontFamily: 'Inter_500Medium',
    fontSize: 15,
    color: PRIMARY_FIXED,
    marginBottom: 10,
    lineHeight: 22,
  },
  narrativeBody: {
    fontFamily: 'Inter_400Regular',
    fontSize: 13,
    color: ON_SURFACE,
    lineHeight: 20,
    marginBottom: 6,
  },
  loadingOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(11, 19, 38, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 100,
  }
});
