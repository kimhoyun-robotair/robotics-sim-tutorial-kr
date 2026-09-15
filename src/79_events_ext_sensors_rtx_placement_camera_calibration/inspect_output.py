"""Inspect actual native calibration.json and report projection residuals."""
import argparse
import json
import math
from pathlib import Path


def matrix(value, rows: int, cols: int, name: str) -> list:
    if not isinstance(value, list) or len(value) != rows:
        raise ValueError(f'{name}: expected {rows} rows')
    if any(not isinstance(row, list) or len(row) != cols for row in value):
        raise ValueError(f'{name}: expected {cols} columns')
    if any(not isinstance(x, (int, float)) or not math.isfinite(x) for row in value for x in row):
        raise ValueError(f'{name}: all entries must be finite numbers')
    return value


def inspect(path: Path) -> dict:
    data = json.loads(path.read_text())
    sensors = data['sensors']
    if not sensors:
        raise ValueError('No cameras found in calibration.json')
    report = []
    for sensor in sensors:
        intrinsic = matrix(sensor['intrinsicMatrix'], 3, 3, 'intrinsicMatrix')
        extrinsic = matrix(sensor['extrinsicMatrix'], 3, 4, 'extrinsicMatrix')
        projection = matrix(sensor['cameraMatrix'], 3, 4, 'cameraMatrix')
        matrix(sensor['homography'], 3, 3, 'homography')
        image_points, world_points = sensor['imageCoordinates'], sensor['globalCoordinates']
        if len(image_points) != len(world_points) or len(image_points) < 6:
            raise ValueError('Expected at least six matching calibration dot pairs')
        errors = []
        for image_point, world_point in zip(image_points, world_points):
            world = [world_point[k] for k in ('x','y','z')] + [1]
            pixel = [sum(row[j] * world[j] for j in range(4)) for row in projection]
            if abs(pixel[2]) < 1e-12:
                raise ValueError('Dot projects to infinity')
            errors.append(math.hypot(pixel[0] / pixel[2] - image_point['x'],
                                     pixel[1] / pixel[2] - image_point['y']))
        product = [[sum(intrinsic[i][k] * extrinsic[k][j] for k in range(3)) for j in range(4)] for i in range(3)]
        denominator = sum(x*x for row in projection for x in row)
        if denominator == 0:
            raise ValueError('Zero projection matrix')
        scale = sum(projection[i][j] * product[i][j] for i in range(3) for j in range(4)) / denominator
        residual = math.sqrt(sum((scale * projection[i][j] - product[i][j])**2 for i in range(3) for j in range(4)))
        report.append({'id': sensor['id'], 'dot_pairs': len(errors), 'max_reprojection_error_px': max(errors),
                       'projection_vs_intrinsic_extrinsic_residual': residual, 'place': sensor['place']})
    return {'camera_count': len(report), 'cameras': report,
            'note': 'Residuals inspect exported data consistency; they do not prove visibility or real-camera calibration accuracy.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', type=Path, help='Native calibration.json export')
    args = parser.parse_args()
    print(json.dumps(inspect(args.path), ensure_ascii=False, indent=2))
