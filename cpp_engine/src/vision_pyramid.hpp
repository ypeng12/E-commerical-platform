#ifndef VISION_PYRAMID_HPP
#define VISION_PYRAMID_HPP

#include <string>
#include <vector>
#include <chrono>
#include <cstdint>
#include <cstddef>

struct VisionResult {
    double composite_score;
    double latency_ms;
    double phash_score;
    double dhash_score;
    double sift_score;
    int kp1_count;
    int kp2_count;
    int matches_count;
    double ssim_score;
    double delta_e;
    std::string verdict;
    std::string engine_type;
};

// AVX2 Vectorized Math Utilities
float simd_avx2_l2_distance_sq(const float* a, const float* b, size_t size);
float simd_avx2_dot_product(const float* a, const float* b, size_t size);

class VisionPyramidEngine {
public:
    VisionPyramidEngine();
    ~VisionPyramidEngine();

    VisionResult match_images(const std::string& image_path_a, const std::string& image_path_b);
    std::string to_json(const VisionResult& result);
};

#endif // VISION_PYRAMID_HPP
