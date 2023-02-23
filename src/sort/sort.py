"""
As implemented in https://github.com/abewley/sort but with some modifications
"""

from __future__ import print_function

import numpy as np
from src.sort.data_association import associate_detections_to_trackers
from src.sort.kalman_tracker import KalmanBoxTracker

class Sort:

    def __init__(self, max_age=10, min_hits=3):
        """
        Sets key parameters for SORT
        """
        self.max_age = max_age
        self.min_hits = min_hits
        self.trackers = []
        self.frame_count = 0

    def update_face_info(self, id, name, conf, feature):
        for trk in self.trackers:
            if trk.id+1 == id:
                return trk.update_face_info(name, conf, feature)
        return False 

    def update(self, dets):
        """
        Params:
          dets - a numpy array of detections in the format [[x,y,x+w,y+h,score],[x,y,x+w,y+h,score],...]
          img_size - [h, w]
        Requires: this method must be called once for each frame even with empty detections.
        Returns the a similar array, where the last column is the object ID.

        NOTE:as in practical realtime MOT, the detector doesn't run on every single frame
        """
        self.frame_count += 1
        # get predicted locations from existing trackers.
        trks = np.zeros((len(self.trackers), 5))
        to_del = []
        for t, trk in enumerate(trks):
            pos = self.trackers[t].predict()  # kalman predict ,very fast ,<1ms
            trk[:] = [pos[0], pos[1], pos[2], pos[3], 0]
            if np.any(np.isnan(pos)):
                to_del.append(t)
        trks = np.ma.compress_rows(np.ma.masked_invalid(trks))
        for t in reversed(to_del):
            self.trackers.pop(t)

        ret = np.zeros((len(dets), 6))
        if dets != []:
            matched, unmatched_dets, unmatched_trks = associate_detections_to_trackers(dets, trks)

            # update matched trackers with assigned detections
            for t, trk in enumerate(self.trackers):
                if t not in unmatched_trks:
                    d = matched[np.where(matched[:, 1] == t)[0], 0]
                    trk.update(dets[d, :][0])

                    det = trk.get_state()
                    ret[d[0]] = np.concatenate((det, [trk.id+1, trk.hits])).reshape(1, -1)

            # create and initialise new trackers for unmatched detections
            for i in unmatched_dets:
                trk = KalmanBoxTracker(dets[i, :])
                self.trackers.append(trk)

                det = trk.get_state()
                ret[i] = np.concatenate((det, [trk.id+1, trk.hits])).reshape(1, -1)
        else:
            ret = np.zeros((len(self.trackers), 6))
            for t, trk in enumerate(self.trackers):
                det = trk.get_state()
                ret[t] = np.concatenate((det, [trk.id+1, trk.hits])).reshape(1, -1)

        i = len(self.trackers)
        for trk in reversed(self.trackers):
            d = trk.get_state()
            i -= 1
            # remove dead tracklet
            if trk.time_since_update >= self.max_age:
                self.trackers.pop(i)

        return ret

    def get_all(self):
        ret = []
        for trk in self.trackers:
            det = trk.get_state()
            face_info = trk.get_face_info()
            arr = [float(d) for d in det]
            arr.extend([trk.id+1, trk.hits])
            arr.extend(face_info)
            ret.append(arr)
        return ret 
