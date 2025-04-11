from sklearn.cluster import KMeans


class TeamAssigner:
    def __init__(self):
        self.team_colors = {}  # culorile celor 2 echipe
        self.player_team_dict = {}

    def clustering_model(self, image):

        # Imaginea devine o matrice 2D( pixel * RGB)
        image_2d = image.reshape(-1, 3)

        # Grupam pixelii in 2 clustere
        # n_init = 10 => este repetat de 10 ori
        kmeans = KMeans(n_clusters=2, init="k-means++",
                        n_init=10).fit(image_2d)

        return kmeans

    def get_player_color(self, frame, bbox):

        # Luam doar tricoul jucatorului
        image = frame[int(bbox[1]): int(bbox[3]), int(bbox[0]):int(bbox[2])]
        top_half_image = image[0:int(image.shape[0]/2), :]

        # Stabilim care este culoare principala de pe tricou
        kmeans = self.clustering_model(top_half_image)
        labels = kmeans.labels_
        clustered_image = labels.reshape(
            top_half_image.shape[0], top_half_image.shape[1])

        # Identificam culoarea fundalului ( gasit adesea in colturi)
        corner_clusters = [clustered_image[0, 0], clustered_image[0, -1],
                           clustered_image[-1, 0], clustered_image[-1, -1]]
        non_player_cluster = max(set(corner_clusters),
                                 key=corner_clusters.count)
        player_cluster = 1 - non_player_cluster
        player_color = kmeans.cluster_centers_[player_cluster]

        return player_color

    def assign_team_color(self, frame, player_detections):

        player_colors = []
        for _, player_detection in player_detections.items():
            bbox = player_detection["bbox"]
            player_color = self.get_player_color(frame, bbox)
            player_colors.append(player_color)

        # Clustering pentru a separa jucatorii in 2 echipe
        kmeans = KMeans(n_clusters=2, init="k-means++",
                        n_init=10).fit(player_colors)

        self.kmeans = kmeans

        self.team_colors[1] = kmeans.cluster_centers_[0]
        self.team_colors[2] = kmeans.cluster_centers_[1]

    def get_player_team(self, frame, player_bbox, player_id):
        # Verificam daca stim deja echipa
        if player_id in self.player_team_dict:
            return self.player_team_dict[player_id]

        player_color = self.get_player_color(frame, player_bbox)

        team_id = self.kmeans.predict(player_color.reshape(1, -1))[0]

        team_id += 1

        # Hardcodare pentru portarul din prima echipa
        if player_id == 89:
            team_id = 1

        self.player_team_dict[player_id] = team_id

        return team_id
