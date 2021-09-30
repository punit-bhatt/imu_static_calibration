import numpy as np
import os
import rosbag

def get_norm_imu_readings(file_path, topic):
    """Get the normalized IMU readings (linear acceleration and angular
    velocities) for the given topic."""

    bag_files = [file for file in os.listdir(file_path) \
        if file.endswith('.bag')]

    # print(f'{bag_files = }')

    assert len(bag_files) > 0

    linear_accelerations = np.zeros((3, len(bag_files)), dtype=np.float32)
    angular_velocities = np.zeros((3, len(bag_files)), dtype=np.float32)

    for i, file in enumerate(bag_files):

        count = 0
        complete_path = file_path.rstrip('/') + '/' + file

        with rosbag.Bag(complete_path, 'r') as bag:
            for (topic, msg, ts) in bag.read_messages(topics=topic):
                linear_accelerations[0][i] += msg.linear_acceleration.x
                linear_accelerations[1][i] += msg.linear_acceleration.y
                linear_accelerations[2][i] += msg.linear_acceleration.z

                angular_velocities[0][i] += msg.angular_velocity.x
                angular_velocities[1][i] += msg.angular_velocity.y
                angular_velocities[2][i] += msg.angular_velocity.z

                count += 1

        linear_accelerations[:, i] /= count
        angular_velocities[:, i] /= count

    # Normalizing readings.
    linear_accelerations = linear_accelerations / \
        np.sqrt(np.sum(linear_accelerations ** 2, axis = 0))
    angular_velocities = angular_velocities / \
        np.sqrt(np.sum(angular_velocities ** 2, axis = 0))

    return linear_accelerations, angular_velocities

def get_axis_of_rotation(a3_acc, ouster_acc):
    """Gets the axis of rotation by finding the eigen vector lying in the
    nullspace of (ouster_acc - a3_acc).T."""

    assert ouster_acc.shape[0] == 3
    assert a3_acc.shape[0] == 3

    _, _, v_T = np.linalg.svd((ouster_acc - a3_acc).T)

    # Last column of V (corresponding to smallest singular value) = last row of
    # v_T
    return v_T[2].reshape((3, 1))

def get_3d_rotation_angle(a3_acc, ouster_acc, unit_axis):
    """Gets the angle of rotation along the unit axis to go from vector 1 to
    vector 2.
    """

    assert a3_acc.shape[0] == 3
    assert ouster_acc.shape[0] == 3
    assert round(np.sum(unit_axis ** 2), 4) == 1

    normal_ouster = ouster_acc - \
        np.matmul(ouster_acc.T, unit_axis).T * unit_axis
    normal_a3 = a3_acc - np.matmul(a3_acc.T, unit_axis).T * unit_axis

    mag_a3 = np.sqrt(np.sum(normal_a3 ** 2, axis = 0))
    mag_ouster = np.sqrt(np.sum(normal_ouster ** 2, axis = 0))

    thetas = np.arccos(np.sum(normal_ouster * normal_a3, axis = 0) / \
        (mag_a3 * mag_ouster))

    return float(np.mean(thetas))

def get_rotation_matrix(omega, theta):
    """Generates the rotation matrix from axis-angle representation using
    Rodrigues' formula
    (https://en.wikipedia.org/wiki/Rodrigues%27_rotation_formula)."""

    assert omega.shape == (3, 1)
    assert round(np.sum(omega ** 2), 4) == 1

    # Skew symmetric matrix.
    _omega = np.array([[0, -float(omega[2]), float(omega[1])],
                       [float(omega[2]), 0, -float(omega[0])],
                       [-float(omega[1]), float(omega[0]), 0]])

    sin = np.sin(theta)
    cos = np.cos(theta)
    R = np.eye(3) + sin * _omega + (1 - cos) * np.matmul(_omega, _omega)

    return R

def verify_rotation_matrix(a3_acc, ouster_acc, R):
    """Verifies the validity of the rotation matrix using A3_Acc = R*Ouster_Acc.
    """

    assert ouster_acc.shape[0] == 3
    assert a3_acc.shape[0] == 3
    assert R.shape == (3, 3)

    print('\nVerifying - ')

    a3_acc_calc = np.matmul(R, ouster_acc)
    mse = np.mean((a3_acc - a3_acc_calc) ** 2)
    diff = np.abs(a3_acc - a3_acc_calc)
    abs_diff_min = np.min(diff)
    abs_diff_max = np.max(diff)
    abs_diff_mean = np.mean(diff)
    abs_diff_std = np.std(diff)

    # print(f'{a3_acc = }')
    # print(f'{a3_acc_calc = }')

    # Error stats
    print(f'{mse = }')
    print(f'{abs_diff_min = }')
    print(f'{abs_diff_max = }')
    print(f'{abs_diff_mean = }')
    print(f'{abs_diff_std = }')

    return mse, abs_diff_min, abs_diff_max, abs_diff_mean, abs_diff_std

def write_matrix_to_file(out_path, R, a3_acc = None, ouster_acc = None):

    with open(out_path, 'w') as f:
        f.write('R -\n{0}\n'.format(R))

    if a3_acc is not None and ouster_acc is not None:
        mse, abs_diff_min, abs_diff_max, abs_diff_mean, abs_diff_std = \
            verify_rotation_matrix(a3_acc, ouster_acc, R)

        with open(out_path, 'a') as f:
            f.write('\nmse - {0}'.format(mse))
            f.write('\nabs_diff_min - {0}'.format(abs_diff_min))
            f.write('\nabs_diff_max - {0}'.format(abs_diff_max))
            f.write('\nabs_diff_mean - {0}'.format(abs_diff_mean))
            f.write('\nabs_diff_std - {0}'.format(abs_diff_std))