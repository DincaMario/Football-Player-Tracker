from utils import get_center_of_bbox, measure_distance


class PlayerBallAssigner():
    # Distanta maxima pentru a stabili jucatorul care este in posesia mingii
    def __init__(self):
        self.max_player_ball_distance = 70

    def assign_ball_to_player(self, players, ball_bbox):
        # Obtinem pozitia mingii
        ball_position = get_center_of_bbox(ball_bbox)

        # assigned_player = -1 => Nimeni nu detine mingea la inceput
        minimum_distance = 9999999999999
        assigned_player = -1

        for player_id, player in players.items():
            # Calculam distanta de la fiecare jucator ( in functie de picior) pana la minge

            player_bbox = player['bbox']
            distance_left = measure_distance(
                (player_bbox[0], player_bbox[-1]), ball_position)
            distance_right = measure_distance(
                (player_bbox[2], player_bbox[- 1]), ball_position)

            # Luam jucatorul cu distanta cea mai mica, cu conditia sa fie mai mica si decat: "max_player_ball_distance"

            distance = min(distance_left, distance_right)
            if distance < self.max_player_ball_distance:
                if distance < minimum_distance:
                    minimum_distance = distance
                    assigned_player = player_id

        return assigned_player
