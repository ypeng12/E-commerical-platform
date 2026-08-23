#ifndef VISION_PYRAMID_HPP
#define VISION_PYRAMID_HPP

#include <string>
#include <vector>
#include <chrono>

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
};

class VisionPyramidEngine {
public:
    VisionPyramidEngine();
    ~VisionPyramidEngine();

    VisionResult match_images(const std::string& image_path_a, const std::string& image_path_b);
    std::string to_json(const VisionResult& result);
};

#endif // VISION_PYRAMID_HPP
