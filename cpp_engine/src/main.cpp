#include "vision_pyramid.hpp"
#include <iostream>

int main(int argc, char** argv) {
    std::string img_a = (argc > 1) ? argv[1] : "sample_gucci.jpg";
    std::string img_b = (argc > 2) ? argv[2] : "sample_gucci.jpg";

    VisionPyramidEngine engine;
    VisionResult result = engine.match_images(img_a, img_b);

    std::cout << engine.to_json(result) << std::endl;
    return 0;
}
