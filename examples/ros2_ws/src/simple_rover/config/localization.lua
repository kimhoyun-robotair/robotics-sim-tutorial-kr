-- 원본의 pure localization 설정을 유지하는 선택용 구성입니다.
-- 사용하려면 저장된 pbstream 상태를 불러오는 별도 launch 구성이 필요합니다.
include "cartographer.lua"
TRAJECTORY_BUILDER.pure_localization_trimmer = {
  max_submaps_to_keep = 3,
}
POSE_GRAPH.optimize_every_n_nodes = 20
return options
