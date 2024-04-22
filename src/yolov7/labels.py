from enum import Enum

class COCOLabels(Enum):
    bag_checked = 0
    bag_unchecked = 1
    file_bag_checked = 2
    file_bag_unchecked = 3
    box_checked = 4
    box_unchecked = 5
    id_card = 6
    person = 7