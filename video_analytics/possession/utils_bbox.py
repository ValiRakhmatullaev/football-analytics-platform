"""
Bbox and distance helpers for possession (Football-Game-Possession-Traking).
bbox format: [x1, y1, x2, y2].
"""


def get_center_of_bbox(bbox):
    x1, y1, x2, y2 = bbox[0], bbox[1], bbox[2], bbox[3]
    return (x1 + x2) / 2, (y1 + y2) / 2


def get_bbox_width(bbox):
    return bbox[2] - bbox[0]


def get_bbox_height(bbox):
    return bbox[3] - bbox[1]


def get_foot_position(bbox):
    x1, y1, x2, y2 = bbox[0], bbox[1], bbox[2], bbox[3]
    return (x1 + x2) / 2, bbox[3]


def measure_distance(p1, p2):
    return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5


def measure_xy_distance(p1, p2):
    return p1[0] - p2[0], p1[1] - p2[1]
