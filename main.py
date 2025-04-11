# Importam clasele necesare aplicatiei

from utils import read_video, save_video
from trackers import Tracker
from Asignare_echipa import TeamAssigner
from Asignare_minge_jucator import PlayerBallAssigner
import numpy as np


def main():

    # Citim video-ul
    video_frames = read_video("Clip_test\8fd33_4.mp4")
    # Oferim track-erului modelul pe care l-am antrenat
    tracker = Tracker('modele/bestFINAL.pt')
    tracks = tracker.get_object_tracks(
        video_frames, read_from_stub=True, stub_path='stubs/tracks_stubs_final.pkl')

    # Interpolare liniara asupra mingii
    tracks["ball"] = tracker.interpolate_ball_positions(tracks["ball"])

    # Stabilim echipa din care face parte fiecare jucator in functie de culoare predominanta a tricoului acestuia
    team_assigner = TeamAssigner()
    team_assigner.assign_team_color(video_frames[0], tracks["players"][0])

    for frame_num, player_track in enumerate(tracks['players']):
        for player_id, track in player_track.items():
            team = team_assigner.get_player_team(
                video_frames[frame_num], track['bbox'], player_id)
            tracks['players'][frame_num][player_id]['team'] = team
            tracks['players'][frame_num][player_id]['team_color'] = team_assigner.team_colors[team]

    # Asignam mingea unui jucator
    player_assigner = PlayerBallAssigner()

    team_ball_control = []

    for frame_num, player_track in enumerate(tracks['players']):
        ball_bbox = tracks['ball'][frame_num][1]['bbox']
        assigned_player = player_assigner.assign_ball_to_player(
            player_track, ball_bbox)

        if assigned_player != -1:
            tracks['players'][frame_num][assigned_player]['has_ball'] = True
            team_ball_control.append(
                tracks['players'][frame_num][assigned_player]['team'])
        else:
            team_ball_control.append(team_ball_control[-1])

    team_ball_control = np.array(team_ball_control)

    output_video_frames = tracker.draw_annotations(
        video_frames, tracks, team_ball_control)

    # Salvam video-ul
    save_video(output_video_frames, 'output_videos/output_video.avi')


if __name__ == '__main__':
    main()
