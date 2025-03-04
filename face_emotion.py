import cv2
from fer import FER
import queue
import time
from flask import session

class EmotionDetector:
    def __init__(self):
        self.detector = FER(mtcnn=True)
        self.frame_queue = queue.Queue()
        self.is_running = False
        self.processed_frame = None
        self.emotion_summary = {"total_faces": 0, "emotions": {"angry": 0, "disgust": 0, "fear": 0, "happy": 0, "sad": 0, "surprise": 0, "neutral": 0}}
        self.current_session_id = None

    def start_session(self):
        if not self.is_running:
            self.is_running = True
            self.emotion_summary = {"total_faces": 0, "emotions": {"angry": 0, "disgust": 0, "fear": 0, "happy": 0, "sad": 0, "surprise": 0, "neutral": 0}}
            from database_setup import get_db_connection
            conn = get_db_connection()
            if conn:
                try:
                    with conn.cursor() as cursor:
                        cursor.execute("INSERT INTO sessions (user_id) VALUES (%s) RETURNING id", (session.get('user_id'),))
                        self.current_session_id = cursor.fetchone()['id']
                        conn.commit()
                except Exception as e:
                    print(f"Error starting session: {e}")
                finally:
                    conn.close()
            return True
        return False

    def stop_session(self):
        if self.is_running:
            self.is_running = False
            from database_setup import get_db_connection
            conn = get_db_connection()
            if conn and self.current_session_id:
                try:
                    with conn.cursor() as cursor:
                        cursor.execute(
                            "UPDATE sessions SET end_time = CURRENT_TIMESTAMP, total_faces = %s, most_common_emotion = %s WHERE id = %s",
                            (self.emotion_summary["total_faces"], max(self.emotion_summary["emotions"], key=self.emotion_summary["emotions"].get), self.current_session_id)
                        )
                        cursor.execute(
                            "UPDATE dashboard_stats SET total_sessions = total_sessions + 1, total_faces_detected = total_faces_detected + %s, most_common_emotion = %s, last_updated = CURRENT_TIMESTAMP WHERE id = 1",
                            (self.emotion_summary["total_faces"], max(self.emotion_summary["emotions"], key=self.emotion_summary["emotions"].get))
                        )
                        conn.commit()
                except Exception as e:
                    print(f"Error stopping session: {e}")
                finally:
                    conn.close()

    def process_frame(self):
        while not self.frame_queue.empty():
            frame = self.frame_queue.get()
            try:
                emotions = self.detector.detect_emotions(frame)
                if emotions:
                    self.emotion_summary["total_faces"] += len(emotions)
                    for face in emotions:
                        dominant_emotion = max(face['emotions'], key=face['emotions'].get)
                        self.emotion_summary["emotions"][dominant_emotion] += 1
                        cv2.rectangle(frame, (face['box'][0], face['box'][1]), 
                                    (face['box'][0] + face['box'][2], face['box'][1] + face['box'][3]), 
                                    (0, 255, 0), 2)
                        cv2.putText(frame, dominant_emotion, (face['box'][0], face['box'][1] - 10), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                self.processed_frame = frame
                if self.current_session_id and emotions:
                    from database_setup import get_db_connection
                    conn = get_db_connection()
                    if conn:
                        try:
                            with conn.cursor() as cursor:
                                for face in emotions:
                                    dominant_emotion = max(face['emotions'], key=face['emotions'].get)
                                    cursor.execute(
                                        "INSERT INTO emotion_logs (session_id, emotion) VALUES (%s, %s)",
                                        (self.current_session_id, dominant_emotion)
                                    )
                                conn.commit()
                        except Exception as e:
                            print(f"Error logging emotions: {e}")
                        finally:
                            conn.close()
            except Exception as e:
                print(f"Error processing frame: {e}")