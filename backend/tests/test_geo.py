from app.services.geo import distance_meters


def test_distance_meters_for_same_point_is_zero():
    assert distance_meters(-1.1452, 36.9561, -1.1452, 36.9561) == 0


def test_distance_meters_for_nearby_points_is_reasonable():
    distance = distance_meters(-1.1452, 36.9561, -1.1462, 36.9561)
    assert 100 <= distance <= 130

