import math
import time
import threading
from collections import defaultdict
 
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.animation import FuncAnimation
 
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
 
from nav_msgs.msg import Odometry, Path
from geometry_msgs.msg import PoseStamped, Point
from visualization_msgs.msg import MarkerArray, Marker
from std_msgs.msg import ColorRGBA, Header
 
try:
    from eufs_msgs.msg import ConeArrayWithCovariance, ConeWithCovariance
    EUFS_MSGS_AVAILABLE = True
except ImportError:
    EUFS_MSGS_AVAILABLE = False
    import warnings
    warnings.warn(
        "eufs_msgs not found. Cone subscription disabled; "
        "only odometry will drive the graph.",
        stacklevel=2,
    )
 
import gtsam
from gtsam import (
    ISAM2,
    ISAM2Params,
    NonlinearFactorGraph,
    Values,
    Pose2,
    Point2,
    symbol_shorthand,
)
from gtsam.noiseModel import Diagonal, Isotropic
 
 
X = symbol_shorthand.X
L = symbol_shorthand.L
 
 
ODOM_NOISE_XY   = 0.05
ODOM_NOISE_THETA = 0.02
CONE_NOISE_XY   = 0.15
 
PRIOR_NOISE     = Diagonal.Sigmas(np.array([0.001, 0.001, 0.001]))
ODOM_NOISE_MODEL = Diagonal.Sigmas(np.array([ODOM_NOISE_XY,
                                              ODOM_NOISE_XY,
                                              ODOM_NOISE_THETA]))
CONE_NOISE_MODEL = Isotropic.Sigma(2, CONE_NOISE_XY)
 
POSE_STEP_DIST   = 0.5
POSE_STEP_ANGLE  = 0.1
LANDMARK_ASSOC_DIST = 1.0
LOOP_CLOSE_DIST  = 2.0
LOOP_CLOSE_SKIP  = 10
OPTIMIZE_EVERY   = 5

CAR_ARROW_LEN   = 1.5
TRAIL_LENGTH    = 20
 
 
def _quat_to_yaw(q):
    siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny_cosp, cosy_cosp)
 
 
def _pose2_from_odom(msg):
    p = msg.pose.pose.position
    q = msg.pose.pose.orientation
    return Pose2(p.x, p.y, _quat_to_yaw(q))
 
 
def _relative_pose(a, b):
    return a.between(b)
 
 
def _add_noise_pose(delta, rng):
    dx  = delta.x()     + rng.normal(0, ODOM_NOISE_XY)
    dy  = delta.y()     + rng.normal(0, ODOM_NOISE_XY)
    dth = delta.theta() + rng.normal(0, ODOM_NOISE_THETA)
    return Pose2(dx, dy, dth)
 
 
def _add_noise_point(pt, rng):
    return pt + rng.normal(0, CONE_NOISE_XY, size=2)
 
 
class GraphSLAM:
    def __init__(self):
        params = ISAM2Params()
        params.setRelinearizeThreshold(0.01)
        params.relinearizeSkip = 1
        self._isam = ISAM2(params)
 
        self._graph  = NonlinearFactorGraph()
        self._values = Values()
 
        self._rng = np.random.default_rng(42)
 
        self._pose_id   = 0
        self._lm_id     = 0
        self._last_gt_pose = None
        self._last_added_pose = None
 
        self._landmark_positions = {}
        self._cone_map = {}
 
        self._lock = threading.Lock()
        self._opt_poses:     list[tuple[float, float, float]] = []
        self._opt_landmarks: dict[int, tuple[float, float]]   = {}

        self._live_pose: tuple[float, float, float] = (0.0, 0.0, 0.0)
 
        self._factor_count = 0
 
        prior_pose = Pose2(0, 0, 0)
        self._graph.add(gtsam.PriorFactorPose2(X(0), prior_pose, PRIOR_NOISE))
        self._values.insert(X(0), prior_pose)
        self._last_added_pose = prior_pose
        self._opt_poses.append((0.0, 0.0, 0.0))
 
    def process_odometry(self, gt_pose: Pose2) -> bool:
        with self._lock:
            self._live_pose = (gt_pose.x(), gt_pose.y(), gt_pose.theta())

        if self._last_gt_pose is None:
            self._last_gt_pose = gt_pose
            return False
 
        delta_gt    = _relative_pose(self._last_gt_pose, gt_pose)
        delta_noisy = _add_noise_pose(delta_gt, self._rng)
 
        dist  = math.hypot(delta_gt.x(), delta_gt.y())
        angle = abs(delta_gt.theta())
        if dist < POSE_STEP_DIST and angle < POSE_STEP_ANGLE:
            self._last_gt_pose = gt_pose
            return False
 
        self._last_gt_pose = gt_pose
 
        new_id   = self._pose_id + 1
        new_pose = self._last_added_pose.compose(delta_noisy)
 
        self._graph.add(
            gtsam.BetweenFactorPose2(
                X(self._pose_id), X(new_id),
                delta_noisy, ODOM_NOISE_MODEL,
            )
        )
        self._values.insert(X(new_id), new_pose)
 
        self._pose_id        = new_id
        self._last_added_pose = new_pose
        self._factor_count  += 1
 
        self._try_loop_closure(new_id, new_pose)
 
        return True
 
    def process_cones(self, cones_world: list[np.ndarray]):
        if self._last_added_pose is None:
            return
 
        for cone_xy in cones_world:
            noisy_xy = _add_noise_point(cone_xy, self._rng)
            lm_idx   = self._associate_landmark(noisy_xy)
 
            obs_local = self._last_added_pose.transformTo(
                Point2(noisy_xy[0], noisy_xy[1])
            )
 
            self._graph.add(
                gtsam.BearingRangeFactor2D(
                    X(self._pose_id),
                    L(lm_idx),
                    gtsam.Rot2.fromAngle(math.atan2(obs_local[1], obs_local[0])),
                    math.hypot(obs_local[0], obs_local[1]),
                    CONE_NOISE_MODEL,
                )
            )
            self._factor_count += 1
 
    def optimize(self):
        try:
            self._isam.update(self._graph, self._values)
            self._isam.update()
            result = self._isam.calculateEstimate()
 
            self._graph  = NonlinearFactorGraph()
            self._values = Values()
 
            poses = []
            for i in range(self._pose_id + 1):
                key = X(i)
                if result.exists(key):
                    p = result.atPose2(key)
                    poses.append((p.x(), p.y(), p.theta()))
 
            landmarks = {}
            for lm_idx in list(self._landmark_positions.keys()):
                key = L(lm_idx)
                if result.exists(key):
                    pt = result.atPoint2(key)
                    landmarks[lm_idx] = (pt[0], pt[1])
 
            with self._lock:
                self._opt_poses     = poses
                self._opt_landmarks = landmarks
 
        except Exception:
            pass
 
    def get_results(self):
        with self._lock:
            return list(self._opt_poses), dict(self._opt_landmarks)

    def get_live_pose(self) -> tuple[float, float, float]:
        with self._lock:
            return self._live_pose
 
    def _associate_landmark(self, xy: np.ndarray) -> int:
        best_idx  = None
        best_dist = LANDMARK_ASSOC_DIST
 
        for lm_idx, lm_xy in self._landmark_positions.items():
            d = np.linalg.norm(xy - lm_xy)
            if d < best_dist:
                best_dist = d
                best_idx  = lm_idx
 
        if best_idx is not None:
            self._landmark_positions[best_idx] = (
                0.7 * self._landmark_positions[best_idx] + 0.3 * xy
            )
            return best_idx
 
        lm_idx = self._lm_id
        self._lm_id += 1
        self._landmark_positions[lm_idx] = xy.copy()
        self._values.insert(L(lm_idx), Point2(xy[0], xy[1]))
        return lm_idx
 
    def _try_loop_closure(self, new_id: int, new_pose: Pose2):
        if new_id < LOOP_CLOSE_SKIP + 2:
            return
        search_ids = range(0, new_id - LOOP_CLOSE_SKIP)
        for old_id in search_ids:
            if old_id >= len(self._opt_poses):
                break
            ox, oy, _ = self._opt_poses[old_id]
            dist = math.hypot(new_pose.x() - ox, new_pose.y() - oy)
            if dist < LOOP_CLOSE_DIST:
                old_pose = Pose2(ox, oy, self._opt_poses[old_id][2])
                delta    = _relative_pose(old_pose, new_pose)
                lc_noise = Diagonal.Sigmas(np.array([0.2, 0.2, 0.05]))
                self._graph.add(
                    gtsam.BetweenFactorPose2(
                        X(old_id), X(new_id), delta, lc_noise
                    )
                )
 
 
class GraphSLAMNode(Node):
 
    def __init__(self):
        super().__init__("graph_slam_node")
        self.get_logger().info("Graph SLAM node starting …")
 
        self._slam = GraphSLAM()
        self._new_factors = 0
 
        qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )
 
        self._odom_sub = self.create_subscription(
            Odometry,
            "/ground_truth/odom",
            self._odom_cb,
            qos,
        )
 
        if EUFS_MSGS_AVAILABLE:
            self._cone_sub = self.create_subscription(
                ConeArrayWithCovariance,
                "/ground_truth/cones",
                self._cone_cb,
                qos,
            )
 
        self._path_pub = self.create_publisher(Path, "/slam/path", 10)
        self._lm_pub   = self.create_publisher(MarkerArray, "/slam/landmarks", 10)
        self._pose_pub = self.create_publisher(PoseStamped, "/slam/pose", 10)
 
        self._opt_timer = self.create_timer(0.5, self._optimize_and_publish)
 
        self._viz_thread = threading.Thread(target=self._run_viz, daemon=True)
        self._viz_thread.start()
 
        self.get_logger().info("Graph SLAM node ready.")
 
    def _odom_cb(self, msg: Odometry):
        gt_pose = _pose2_from_odom(msg)
        added   = self._slam.process_odometry(gt_pose)
        if added:
            self._new_factors += 1
 
    def _cone_cb(self, msg):
        if self._slam._last_gt_pose is None:
            return
 
        cur = self._slam._last_gt_pose
        cones_world = []
 
        all_cones = (
            list(msg.blue_cones)
            + list(msg.yellow_cones)
            + list(msg.orange_cones)
            + list(msg.big_orange_cones)
            + list(msg.unknown_color_cones)
        )
 
        for cone in all_cones:
            lx, ly = cone.point.x, cone.point.y
            wx = cur.x() + lx * math.cos(cur.theta()) - ly * math.sin(cur.theta())
            wy = cur.y() + lx * math.sin(cur.theta()) + ly * math.cos(cur.theta())
            cones_world.append(np.array([wx, wy]))
 
        self._slam.process_cones(cones_world)
        self._new_factors += len(cones_world)
 
    def _optimize_and_publish(self):
        if self._new_factors < OPTIMIZE_EVERY:
            return
        self._new_factors = 0
 
        self._slam.optimize()
        poses, landmarks = self._slam.get_results()
 
        now = self.get_clock().now().to_msg()
 
        path_msg = Path()
        path_msg.header.frame_id = "map"
        path_msg.header.stamp    = now
        for (x, y, th) in poses:
            ps = PoseStamped()
            ps.header.frame_id = "map"
            ps.header.stamp    = now
            ps.pose.position.x = x
            ps.pose.position.y = y
            ps.pose.orientation.z = math.sin(th / 2)
            ps.pose.orientation.w = math.cos(th / 2)
            path_msg.poses.append(ps)
        self._path_pub.publish(path_msg)
 
        if poses:
            x, y, th = poses[-1]
            ps = PoseStamped()
            ps.header.frame_id = "map"
            ps.header.stamp    = now
            ps.pose.position.x = x
            ps.pose.position.y = y
            ps.pose.orientation.z = math.sin(th / 2)
            ps.pose.orientation.w = math.cos(th / 2)
            self._pose_pub.publish(ps)
 
        ma = MarkerArray()
        for lm_id, (lx, ly) in landmarks.items():
            m = Marker()
            m.header.frame_id = "map"
            m.header.stamp    = now
            m.ns              = "landmarks"
            m.id              = lm_id
            m.type            = Marker.CYLINDER
            m.action          = Marker.ADD
            m.pose.position.x = lx
            m.pose.position.y = ly
            m.pose.position.z = 0.15
            m.scale.x = m.scale.y = 0.3
            m.scale.z = 0.5
            m.color.r = 1.0
            m.color.g = 0.6
            m.color.b = 0.0
            m.color.a = 0.9
            ma.markers.append(m)
        self._lm_pub.publish(ma)
 
    def _run_viz(self):
        plt.ion()
        fig, ax = plt.subplots(figsize=(10, 8))
        fig.patch.set_facecolor("#1a1a2e")
        ax.set_facecolor("#16213e")
        ax.set_title("Graph SLAM — Live View", color="white", fontsize=14, pad=12)
        ax.tick_params(colors="white")
        for spine in ax.spines.values():
            spine.set_edgecolor("#444")
 
        path_line,   = ax.plot([], [], "-", color="#00d4ff", lw=1.5,
                               label="Optimised path", zorder=2)
        pose_scatter  = ax.scatter([], [], s=18, c="#00d4ff", zorder=3,
                                   label="Pose nodes")
        lm_scatter    = ax.scatter([], [], s=60, c="#ff6b35", marker="^",
                                   zorder=4, label="Landmarks")

        trail_line,  = ax.plot([], [], "-", color="#ffe600", lw=2.5,
                               alpha=0.55, zorder=4, label="Recent trail")

        car_dot,     = ax.plot([], [], "o", color="#ffe600", ms=13,
                               markeredgecolor="white", markeredgewidth=1.5,
                               label="Car (live)", zorder=6)

        arrow_container = [None]

        ellipses = []
 
        ax.legend(loc="upper left", facecolor="#0f3460", edgecolor="#444",
                  labelcolor="white", fontsize=9)
        ax.set_aspect("equal", "datalim")
        ax.set_xlabel("X (m)", color="white")
        ax.set_ylabel("Y (m)", color="white")
 
        def _update(_frame):
            nonlocal ellipses

            poses, landmarks = self._slam.get_results()
            cx, cy, cth = self._slam.get_live_pose()

            if not poses:
                return
 
            xs = [p[0] for p in poses]
            ys = [p[1] for p in poses]
 
            path_line.set_data(xs, ys)
            pose_scatter.set_offsets(
                np.column_stack([xs, ys]) if len(xs) > 1
                else np.array([[xs[0], ys[0]]])
            )

            tail = poses[-TRAIL_LENGTH:] if len(poses) > 1 else poses
            trail_line.set_data([p[0] for p in tail], [p[1] for p in tail])
 
            if landmarks:
                lx = [v[0] for v in landmarks.values()]
                ly = [v[1] for v in landmarks.values()]
                lm_scatter.set_offsets(np.column_stack([lx, ly]))

            car_dot.set_data([cx], [cy])

            if arrow_container[0] is not None:
                arrow_container[0].remove()
            arrow_len = CAR_ARROW_LEN
            dx = arrow_len * math.cos(cth)
            dy = arrow_len * math.sin(cth)
            arrow_container[0] = ax.annotate(
                "",
                xy=(cx + dx, cy + dy),
                xytext=(cx, cy),
                arrowprops=dict(
                    arrowstyle="-|>",
                    color="#ffe600",
                    lw=2.2,
                    mutation_scale=18,
                ),
                zorder=7,
            )
 
            for e in ellipses:
                e.remove()
            ellipses = []
            for i in range(0, len(poses), max(1, len(poses) // 30)):
                px, py, _ = poses[i]
                ell = mpatches.Ellipse(
                    (px, py), 2 * ODOM_NOISE_XY, 2 * ODOM_NOISE_XY,
                    color="#00d4ff", fill=False, alpha=0.25, lw=0.6, zorder=1,
                )
                ax.add_patch(ell)
                ellipses.append(ell)
 
            all_x = xs + [cx] + ([v[0] for v in landmarks.values()] if landmarks else [])
            all_y = ys + [cy] + ([v[1] for v in landmarks.values()] if landmarks else [])
            if all_x:
                pad = 2.0
                ax.set_xlim(min(all_x) - pad, max(all_x) + pad)
                ax.set_ylim(min(all_y) - pad, max(all_y) + pad)
 
            ax.set_title(
                f"Graph SLAM — Poses: {len(poses)}  |  Landmarks: {len(landmarks)}",
                color="white", fontsize=13, pad=10,
            )
 
        anim = FuncAnimation(fig, _update, interval=100, cache_frame_data=False)
        plt.tight_layout()
        plt.show(block=True)
 
 
def main(args=None):
    rclpy.init(args=args)
    node = GraphSLAMNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
 
 
if __name__ == "__main__":
    main()
