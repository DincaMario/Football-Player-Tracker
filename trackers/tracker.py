from ultralytics import YOLO
import supervision as sv
import pickle
import os
import sys
import cv2
import pandas as pd
from utils import get_bbox_width, get_center_of_bbox, get_foot_position
import numpy as np

sys.path.append('../')


class Tracker:
    def __init__(self, model_path):
        self.model = YOLO(model_path)
        self.tracker = sv.ByteTrack()

    # Functia ce se ocupa cu detectarea cadrelor
    def detect_frames(self, frames):
        # Se vor procesa cate 20 de cadre per procesare pentru a evita suprasolicitarea memoriei
        batch_size = 20
        # Array-ul de detectii
        detections = []

        # Parcurgem toate set-urile de frame-uri si analizam fiecare set
        # Doar entitatile cu incredere >= 15% vor fi luate in calcul

        for i in range(0, len(frames), batch_size):
            detections_batch = self.model.predict(
                frames[i:i+batch_size], conf=0.15)
            detections += detections_batch

        return detections

    # Identificarea jucatorilor, arbitrilor si a mingii din teren
    def get_object_tracks(self, frames,  read_from_stub=False, stub_path=None):

        # Verificam daca exista deja un fisier care sa contina datele pentru "tracking"
        if read_from_stub and stub_path is not None and os.path.exists(stub_path):
            with open(stub_path, 'rb') as f:
                tracks = pickle.load(f)
            return tracks

        # Detectam datele din clip
        detections = self.detect_frames(frames)

        tracks = {
            "players": [],
            "referees": [],
            "ball": []
        }

        # Parcurgem fiecare cadru
        for frame_num, detection in enumerate(detections):

            # Creem un dictionar de forma ({'player': 0, referee: 1, 'ball': 2})
            cls_names = detection.names
            clas_names_inv = {v: k for k, v in cls_names.items()}
            print("cls_names:", cls_names)
            print("clas_names_inv:", clas_names_inv)

            # Convertim datele intr-un format "Supervision" din unul YOLO
            detection_supervision = sv.Detections.from_ultralytics(detection)

            # Convertim portarii in jucatori
            for object_ind, class_id in enumerate(detection_supervision.class_id):
                if cls_names[class_id] == "goalkeeper":
                    detection_supervision.class_id[object_ind] = clas_names_inv["player"]

            # Updateaza tracker-ul cu detectarile date si returneaza detectarile actualizate
            detection_with_tracks = self.tracker.update_with_detections(
                detection_supervision)

            tracks["players"].append({})
            tracks["referees"].append({})
            tracks["ball"].append({})

            # Jucatorii si arbitrii sunt track-uiti cu id-uri unice ( track_id )
            for frame_detection in detection_with_tracks:
                bbox = frame_detection[0].tolist()
                cls_id = frame_detection[3]
                track_id = frame_detection[4]

                if cls_id == clas_names_inv['player']:
                    tracks["players"][frame_num][track_id] = {"bbox": bbox}

                if cls_id == clas_names_inv['referee']:
                    tracks["referees"][frame_num][track_id] = {"bbox": bbox}

            # In schimb, deoarece intr-un meci de fotbal poate exista doar o minge, aceasta are un ID fix
            for frame_detection in detection_supervision:
                bbox = frame_detection[0].tolist()
                cls_id = frame_detection[3]

                if cls_id == clas_names_inv['ball']:
                    tracks["ball"][frame_num][1] = {"bbox": bbox}

            print(detection_with_tracks)

        # Se salveaza intr-un fisier
        if stub_path is not None:
            with open(stub_path, 'wb') as f:
                pickle.dump(tracks, f)

        return tracks

    # Functia ce deseneaza o elipsa in jurul fiecarui jucator track-uit
    def draw_ellipse(self, frame, bbox, color, track_id=None):

        y2 = int(bbox[3])
        x_center, _ = get_center_of_bbox(bbox)
        width = get_bbox_width(bbox)

        # Deseneam efectiv elipsa in jurul jucatorului
        cv2.ellipse(frame, center=(x_center, y2),
                    axes=(int(width), int(0.30*width)), angle=0.0, startAngle=-45, endAngle=275, color=color, thickness=2, lineType=cv2.LINE_4)

        # Desenam dreptunghiul care contine ID-ul jucatorului/ arbitrului respectiv
        rectangle_width = 40
        rectangle_height = 20
        x1_rect = x_center - rectangle_width//2
        x2_rect = x_center + rectangle_width//2
        y1_rect = (y2 - rectangle_height//2) + 15
        y2_rect = (y2 + rectangle_height//2) + 15

        if track_id is not None:
            cv2.rectangle(frame,
                          (int(x1_rect), int(y1_rect)),
                          (int(x2_rect), int(y2_rect)),
                          color,
                          cv2.FILLED)

            x1_text = x1_rect+12
            if track_id > 99:
                x1_text -= 10

            cv2.putText(
                frame,
                f"{track_id}",
                (int(x1_text), int(y1_rect+15)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 0),
                2
            )

        return frame

    # Desenam un triunghi deasupra mingei/jucatorului ce are mingea
    def draw_triangle(self, frame, bbox, color):
        y = int(bbox[1])
        x, _ = get_center_of_bbox(bbox)

        triangle_points = np.array([
            [x, y],
            [x + 10, y - 20],
            [x - 10, y - 20],
        ])

        cv2.drawContours(frame, [triangle_points], 0, color, cv2.FILLED)
        cv2.drawContours(frame, [triangle_points], 0, (0, 0, 0), 2)

        return frame

    # Desenam dreptunghiul in afisam procentul de posesie pentru fiecare echipa
    def draw_team_ball_control(self, frame, frame_num, team_ball_control):
        overlay = frame.copy()
        cv2.rectangle(overlay, (1350, 850), (1900, 970), (255, 255, 255), -1)
        alpha = 0.4  # transparenta
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

        team_ball_control_till_frame = team_ball_control[:frame_num + 1]
        team_1_num_frames = team_ball_control_till_frame[team_ball_control_till_frame == 1].shape[0]
        team_2_num_frames = team_ball_control_till_frame[team_ball_control_till_frame == 2].shape[0]

        total_frames = team_2_num_frames + team_1_num_frames

        # Nr. de frame-uri in care echipa i a avut mingea/nr total de frame-uri in care o echipa a avut mingea
        team_1 = team_1_num_frames/total_frames
        team_2 = team_2_num_frames/total_frames

        cv2.putText(frame, f"Team 1 Possesion: {team_1 * 100:.2f}%",
                    (1400, 900), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 3)
        cv2.putText(frame, f"Team 2 Possesion: {team_2 * 100:.2f}%",
                    (1400, 950), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 3)

        return frame

    def draw_annotations(self, video_frames, tracks, team_ball_control):
        output_video_frames = []
        for frame_num, frame in enumerate(video_frames):
            frame = frame.copy()

            player_dict = tracks["players"][frame_num]
            referees_dict = tracks["referees"][frame_num]
            ball_dict = tracks["ball"][frame_num]

            # Desenam jucatorii

            for track_id, player in player_dict.items():
                color = player.get("team_color", (0, 0, 255))
                frame = self.draw_ellipse(
                    frame, player["bbox"], color, track_id)

                if player.get('has_ball', False):
                    frame = self.draw_triangle(
                        frame, player["bbox"], (0, 0, 255))

            # Desenam arbitrii

            for track_id, referee in referees_dict.items():
                frame = self.draw_ellipse(
                    frame, referee["bbox"], (255, 0, 0), track_id)

            # Desenam Mingea

            for track_id, ball in ball_dict.items():
                frame = self.draw_triangle(frame, ball["bbox"], (0, 255, 0))

            # Desenam % de posesie
            frame = self.draw_team_ball_control(
                frame, frame_num, team_ball_control)

            output_video_frames.append(frame)

        return output_video_frames

    # Pentru segmentele in care mingea nu a fost detectata, facem niste predictii referitoare la pozitia acesteia si le afisam
    def interpolate_ball_positions(self, ball_positions):
        # Ia bbox-ul obiectului cu id-ul 1 ( care mereu va fi mingea )
        # Daca nu este gasita, va returna un dictionar gol
        ball_positions = [x.get(1, {}).get('bbox', {})
                          for x in ball_positions]

        # Se pun toate pozitiile intr-un dataframe pentru a putea fi inlocuite valorile NaN prin interpolare
        df_ball_positions = pd.DataFrame(
            ball_positions, columns=['x1', 'y1', 'x2', 'y2'])
        df_ball_positions = df_ball_positions.interpolate()
        df_ball_positions = df_ball_positions.bfill()

        # Apoi sunt aduse in forma initiala
        ball_positions = [{1: {"bbox": x}}
                          for x in df_ball_positions.to_numpy().tolist()]

        return ball_positions
