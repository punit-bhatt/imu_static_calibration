import argparse
import calibration_helper as helper

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-f',
                        '--bag-path',
                        help="Defines the bag file folder path.",
                        required=True)
    parser.add_argument('-ai',
                       '--a3-imu-topic',
                       help="Defines the A3 IMU topic",
                       default='/uav1/dji_sdk/imu')
    parser.add_argument('-oi',
                       '--ouster-imu-topic',
                       help="Defines the horizontal lidar IMU topic",
                       default='/uav1/os_hori/os_cloud_node/imu')
    parser.add_argument('-o',
                       '--out-path',
                       help="Defines the file path to write output to.",
                       default='./matrix.txt')
    args = parser.parse_args()

    bag_path = args.bag_path
    a3_imu_topic = args.a3_imu_topic
    ouster_imu_topic = args.ouster_imu_topic
    out_path = args.out_path

    print(f'{bag_path = }')
    print(f'{a3_imu_topic = }')
    print(f'{ouster_imu_topic = }')

    a3_linear_acc, a3_angular_vel = helper.get_norm_imu_readings(bag_path,
                                                                 a3_imu_topic)
    ouster_linear_acc, ouster_angular_vel = \
        helper.get_norm_imu_readings(bag_path, ouster_imu_topic)

    print(f'{a3_linear_acc.shape = }')
    print(f'{ouster_linear_acc.shape = }')

    omega = helper.get_axis_of_rotation(a3_linear_acc, ouster_linear_acc)
    theta = helper.get_3d_rotation_angle(a3_linear_acc, ouster_linear_acc, omega)
    R = helper.get_rotation_matrix(omega, theta)

    print(f'\n{omega = }')
    print(f'{theta = }')
    print(f'{R = }')

    # helper.verify_rotation_matrix(a3_linear_acc, ouster_linear_acc, R)
    helper.write_matrix_to_file(out_path, R, a3_linear_acc, ouster_linear_acc)